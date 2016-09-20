from collections import OrderedDict
from ..plotting.curves import plot_class_distribution

from itertools import permutations
from itertools import islice
from random import choice
from operator import itemgetter
from operator import add
from random import sample
from random import shuffle


def comp(f, g):
    def wrapped(x):
        return f(g(x))
    return wrapped


def lazy_almost_shuffled_permutations(source, num, shuffle_const=30000):
    perm = permutations(source, num)
    while True:
        slice_of_perm = list(islice(perm, shuffle_const))
        shuffle(slice_of_perm)
        if not slice_of_perm:
            break
        for _sample in slice_of_perm:
            yield _sample


def random_subsampling(source, num):
    n = len(source)
    c = 0
    while c < n * (n - 1):
        x, y = sample(source, num)
        if x != y:
            yield x, y
            c += 1


class ClassificationDataset(object):
    # name of the dataset
    name = None
    # list of lists with samples
    classes = None
    # names of labels
    class_labels = None
    # if train / test directories exist
    is_pre_split = None

    @property
    def class_count(self):
        return len(self.classes)

    def summary(self):
        print("{} dataset wrapper object:".format(self.name))
        print("Number of classes {}".format(self.class_count))
        print("Number of files {}".format(sum(self.get_count_of_classes())))

    def get_count_of_classes(self, with_labels=False):
        counts = map(len, self.classes)
        if with_labels:
            return OrderedDict((self.class_labels[i], c)
                               for i, c in enumerate(counts))
        return counts

    def plot_class_distribution(self):
        freq_dict = self.get_count_of_classes(with_labels=True)
        return plot_class_distribution(freq_dict)

    def make_train_and_test_split(self, testset_ratio, folds=1):
        raise NotImplementedError()
        # if folds == 1:
        #     train_and_test_filenames = [('train_index', 'test_index')]
        # else:
        #     train_and_test_filenames = [
        #         tuple("{0}_index.{1}".format(t, i) for t in ("train", "test"))
        #         for i in range(1, folds + 1)
        #     ]
        # for pair_of_names in train_and_test_filenames:
        #     train_samples, test_samples = [], []
        #     for k, iterator in self.get_samples_grouped_by_class_id():
        #         class_k_samples = list(iterator)
        #         number_of_test_samples = max(int(np.floor(len(class_k_samples) * testset_ratio)), 1)
        #         class_data_permutation = sample(class_k_samples, len(class_k_samples))
        #         train_samples.extend(class_data_permutation[number_of_test_samples:])
        #         test_samples.extend(class_data_permutation[0: number_of_test_samples])
        #     for filename, list_of_samples in zip(pair_of_names,
        #                                          (train_samples, test_samples)):
        #         with open(os.path.join(self.dataset_folder, filename), 'w+') as fh:
        #             fh.write("\n".join(
        #                 "{path} {class_id}".format(**s.__dict__)
        #                 for s in list_of_samples))

    def get_pairs_from_classes(self, method):
        """
        Choose method to sample pairs from same class
        :param method: range from 0 - 2
        :return:
        """
        method_funs = [
            permutations,
            lazy_almost_shuffled_permutations,
            random_subsampling
        ]

        pairs_dict = {
            _i: method_funs[method](_samples, 2)
            for _i, _samples in enumerate(self.classes)
        }
        return pairs_dict

    def generate_triplets(self, batch_size=150, unique_classes_in_batch=5,
                          method=0):
        """ Return list of batch_size samples and list of ranges
        for same class samples
        :param batch_size:
        :param unique_classes_in_batch:
        :param method:
        :return:
        """
        assert unique_classes_in_batch <= self.class_count
        assert batch_size % (unique_classes_in_batch * 3) == 0
        pairs_dict = self.get_pairs_from_classes(method)
        set_of_all_classes = frozenset(pairs_dict)
        trips_for_one_class = batch_size / unique_classes_in_batch  # 30
        num_pairs = trips_for_one_class / 3  # 10
        num_pairs_in_loop = num_pairs
        result_triplets = []
        batch_samples = []
        while pairs_dict:
            try:
                not_used_classes = set(pairs_dict.keys()) -\
                                   set(map(itemgetter(1), result_triplets))
                if not not_used_classes:
                    not_used_classes = set(pairs_dict.keys())
                _pairs_class = choice(list(not_used_classes))
            except IndexError:
                break
            grabbed_pairs = list(
                islice(pairs_dict[_pairs_class], num_pairs_in_loop))
            if len(grabbed_pairs) < num_pairs_in_loop:
                del pairs_dict[_pairs_class]
                if not grabbed_pairs:
                    continue
            result_triplets.append((grabbed_pairs, _pairs_class))
            chunks_length = map(comp(len, itemgetter(0)), result_triplets)
            total_length = sum(chunks_length)
            samples_left = num_pairs * unique_classes_in_batch - total_length
            if not samples_left:
                for _pairs, _pairs_class_it in result_triplets:
                    anchors, positives = zip(*_pairs)
                    batch_samples.extend(anchors)
                    batch_samples.extend(positives)
                    batch_samples.extend(self.get_n_random_samples_from_classes(
                        set_of_all_classes - {_pairs_class_it}, len(anchors)))
                yield batch_samples, chunks_length
                result_triplets = []
                batch_samples = []
                num_pairs_in_loop = num_pairs
            else:
                num_pairs_in_loop = num_pairs if samples_left >= num_pairs \
                    else samples_left

    def get_n_random_samples_from_classes(self, class_ids, n):
        return sample(
            reduce(add, map(self.classes.__getitem__, class_ids)), n)
