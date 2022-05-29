import sys
import unittest
import dirs

class KVTestCase(unittest.TestCase):

    def setUp(self) -> None:
        """
        Initial setup
        """
        return super().setUp()

    def test_convert_win_to_py_path(self)->None:
        """
        Tests convert_win_to_py_path()
        """
        winpath1 = r"D:\User Files\Personal\Cloud Drive\MEGAsync\Nonsensitive\Archive\ios"
        pypath1 = "D:/User Files/Personal/Cloud Drive/MEGAsync/Nonsensitive/Archive/ios"
        winpath2 = r"D:"

        self.assertEqual(pypath1, dirs.convert_win_to_py_path(winpath1))
        self.assertEqual(winpath2, dirs.convert_win_to_py_path(winpath2))

    def test_replace_dots_to_py_path(self) -> None:
        """
        Tests replace_dots_to_py_path(dotspath:str)
        """
        # Current path
        self.assertEqual(dirs.replace_dots_to_py_path("."),  dirs.convert_win_to_py_path(sys.path[0]))

        # Current path + directory
        self.assertEqual(dirs.replace_dots_to_py_path("./img/"),  dirs.convert_win_to_py_path(sys.path[0] + "/img/"))

        # Previous path
        self.assertEqual(dirs.replace_dots_to_py_path(".."),  dirs.convert_win_to_py_path(sys.path[0]).rpartition('/')[0])

        # Previous path + directory
        self.assertEqual(dirs.replace_dots_to_py_path("../img/"),  dirs.convert_win_to_py_path(sys.path[0]).rpartition('/')[0] + '/img/')

        # Current path to file
        self.assertEqual(dirs.replace_dots_to_py_path("./something.txt"),  dirs.convert_win_to_py_path(sys.path[0] + '/something.txt'))


if __name__ == '__main__':
    unittest.main()
