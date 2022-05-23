import unittest
from SKKDownloader import SKK
from unittest.mock import patch
import os
COOKIEDIR = "C:/Users/chenj/Downloads/fun/src/Cookie.txt"  
DOWNPATH = 'C:/Users/chenj/Downloads/fun/img/'
LOG_PATH = r'C:/Users/chenj/Downloads/fun/logs/'

class SKKTestCase(unittest.TestCase):

    def setUp(self) -> None:
        with open (COOKIEDIR,'r') as fd:
            self.SKK = SKK(None, None, {'cookie' : fd.read()}, DOWNPATH)
        
        self.url_norm = 'https://chan.sankakucomplex.com/?tags=persona'
        self.url_normp2 = 'https://chan.sankakucomplex.com/?tags=persona_4&page=2'
        self.url_bad = 'google.com'
        self.url_search = 'https://chan.sankakucomplex.com/?tags=persona_4&commit=Search'
        self.url_img = 'https://chan.sankakucomplex.com/post/show/31149579'
        self.url_normShort = 'https://chan.sankakucomplex.com/?tags=shura+in_visible_pool%3Atrue'
        self.url_normMed = 'https://chan.sankakucomplex.com/?tags=a_channel'
        self.url_normLarge = 'https://chan.sankakucomplex.com/?tags=hunter_x_hunter'
        pass
    
    def test__sankaku_postid_strip(self):
        """
        Tests stripping postids
        """
        expected = '31149579'
        self.assertEqual(expected, self.SKK._SKK__sankaku_postid_strip(self.url_img))
    
    @patch('SKKDownloader.input', create=True)
    def test_set_url(self, mocked_input):
        """
        Tests set_url
        """
        mocked_input.side_effect = [self.url_norm, self.url_bad, self.url_search, self.url_search]
        
        # User input once
        self.SKK.set_url(None)
        self.assertEqual(self.url_norm, self.SKK.get_url())
        
        # User input incorrect then correct
        self.SKK.set_url(self.url_bad)
        self.assertEqual(self.url_search, self.SKK.get_url())

        # Good param given
        self.SKK.set_url(self.url_norm)
        self.assertEqual(self.url_norm, self.SKK.get_url())

        # Bad param then input good param
        self.SKK.set_url(self.url_bad)
        self.assertEqual(self.url_search, self.SKK.get_url())

    def test__convert_link(self):
        """
        Tests __convert_link()
        """
        # Convert a normal link
        partition = self.SKK._SKK__convert_link(self.url_norm)
        self.assertEqual(('https://chan.sankakucomplex.com/', '?next=', '&tags=persona&page=1'), partition)
    
    def test__get_content_links(self):
        """
        Tests __get_content_links()
        """
        # Grab links from home page
        self.assertEqual(24, self.SKK._SKK__get_content_links(self.url_norm, 0))

        # Grab links from non-homepage
        self.SKK.set_url(self.url_normp2)
        self.assertEqual(44, self.SKK._SKK__get_content_links(self.url_normp2, 0))

        # Skip 1 link
        self.assertEqual(63, self.SKK._SKK__get_content_links(self.url_normp2, 1))

        # Skip all links
        self.assertEqual(63, self.SKK._SKK__get_content_links(self.url_normp2, 20))
    
    def test__process_container(self):
        """
        Tests __process_container()
        """

        # Short
        #self.SKK.set_url(self.url_normShort)
        #self.SKK._SKK__process_container()
        #self.assertEqual(807, self.SKK._SKK__get_content_links(self.url_normp2, 20))
        #self.setUp()
        # Medium
        #self.SKK.set_url(self.url_normMed)
        #self.SKK._SKK__process_container()
        #self.assertEqual(961, self.SKK._SKK__get_content_links(self.url_normp2, 20))
        #self.setUp()
        # Large 
        #self.SKK.set_url(self.url_normLarge)
        #self.SKK._SKK__process_container()
        #self.assertEqual(69, self.SKK._SKK__get_content_links(self.url_normp2, 20))
    
    def test__get_content_src(self):
        """
        Tests __get_content_src()
        """
        img1 = 'https://chan.sankakucomplex.com/post/show/31149921'
        img2 = 'https://chan.sankakucomplex.com/post/show/31149908'
        img3 = 'https://chan.sankakucomplex.com/post/show/31149881'
        gif1 = 'https://chan.sankakucomplex.com/post/show/31131654'
        gif2 = 'https://chan.sankakucomplex.com/post/show/31097442'
        video1 = 'https://chan.sankakucomplex.com/post/show/25491005'
        video2 = 'https://chan.sankakucomplex.com/post/show/14249741'
        flash1 = 'https://chan.sankakucomplex.com/post/show/3378073'
        self.assertTrue('https://s.sankakucomplex.com/data/b2/71/b27111f28dd45688e3f5606f065bb8ef.png?' in self.SKK._SKK__get_content_src(img1))
        self.assertTrue('https://s.sankakucomplex.com/data/04/d5/04d54c9596f6455bf992e46fb01a1721.jpg?' in self.SKK._SKK__get_content_src(img2))
        self.assertTrue('https://s.sankakucomplex.com/data/56/de/56deed4ffe394e14dabaf1a5f886a1ee.jpg?' in self.SKK._SKK__get_content_src(img3))
        self.assertTrue('33e56465fc735349564c7b05d7c8da5b.gif?' in self.SKK._SKK__get_content_src(gif1))
        self.assertTrue('1bcc643994e6f38ec042febb4daf29be.gif?' in self.SKK._SKK__get_content_src(gif2))
        self.assertTrue('https://s.sankakucomplex.com/data/bb/d8/bbd8745f73331b02bde16446e5d1a0f1.mp4?' in self.SKK._SKK__get_content_src(video1))
        self.assertTrue('https://s.sankakucomplex.com/data/bb/2d/bb2dcb70641f091ed1b63fba1b103d8e.mp4?' in self.SKK._SKK__get_content_src(video2))
        self.assertTrue('https://v.sankakucomplex.com/data/f6/23/f623ea7559ef39d96ebb0ca7530586b8.swf?e=1652991229&m=59NN640CgVlP1fbDOaiP8Q&expires=1652991229&token=CvsgiF2_LUGS-bPkvuD1tWWSABvBITQwxbtUmuJmBbc', self.SKK._SKK__get_content_src(flash1))
    
    def test__process_content(self):
        """
        Tests __process_content()
        """
        img1 = 'https://chan.sankakucomplex.com/post/show/31149921'
        img2 = 'https://chan.sankakucomplex.com/post/show/31149908'
        img3 = 'https://chan.sankakucomplex.com/post/show/31149881'
        gif1 = 'https://chan.sankakucomplex.com/post/show/31131654'
        gif2 = 'https://chan.sankakucomplex.com/post/show/31097442'
        video1 = 'https://chan.sankakucomplex.com/post/show/25491005'
        video2 = 'https://chan.sankakucomplex.com/post/show/14249741'
        flash1 = 'https://chan.sankakucomplex.com/post/show/3378073'

        self.SKK._SKK__process_content(img1)
        self.SKK._SKK__process_content(img2)
        self.SKK._SKK__process_content(img3)
        self.SKK._SKK__process_content(gif1)
        self.SKK._SKK__process_content(gif2)
        self.SKK._SKK__process_content(video1)
        self.SKK._SKK__process_content(video2)
        self.SKK._SKK__process_content(flash1)

        self.assertEqual(1577457, os.stat(DOWNPATH + "3378073.swf").st_size)
        self.assertEqual(451572, os.stat(DOWNPATH + "25491005.mp4").st_size)
        self.assertEqual(615305, os.stat(DOWNPATH + "31097442.gif").st_size)
        self.assertEqual(7582607, os.stat(DOWNPATH + "31131654.gif").st_size)
        self.assertEqual(2067582, os.stat(DOWNPATH + "31149881.jpg").st_size)
        self.assertEqual(276153, os.stat(DOWNPATH + "31149908.jpg").st_size)
        self.assertEqual(5025539, os.stat(DOWNPATH + "31149921.png").st_size)
        self.assertEqual(6017172, os.stat(DOWNPATH + "14249741.mp4").st_size)


    #def test_run(self):
    #    """
    #    Test a small, mixed test case at default settings
    #    """
    #    self.SKK.set_url('https://chan.sankakucomplex.com/?tags=tentacle+loli+inflation+monster')
    #    self.SKK.run()
if __name__ == '__main__':
    unittest.main()
