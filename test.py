from audioset_download import Downloader

d = Downloader(root_path='test', labels=None, n_jobs=2, download_type='unbalanced_train', copy_and_replicate=False)
d.download(format = 'vorbis')
