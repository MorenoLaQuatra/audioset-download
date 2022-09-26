# AudioSet Download

This repository contains code for downloading the [AudioSet](https://research.google.com/audioset/) dataset.
The code is provided as-is, and is not officially supported by Google.

## Requirements

* Python 3.9 (it may work with other versions, but it has not been tested)

## Installation

```bash
# Install ffmpeg
sudo apt install ffmpeg
# Install audioset-download
pip install audioset-download
```

## Usage

The following code snippet downloads the unbalanced train set, and stores it in the `test` directory.
It only downloads the files associated with the `Speech` and `Afrobeat` labels, and uses two parallel processes for downloading.
If a file is associated to multiple labels, it will be stored only once, and associated to the first label in the list.

```python
from audioset_download import Downloader
d = Downloader(root_path='test', labels=["Speech", "Afrobeat"], n_jobs=2, download_type='unbalanced_train', copy_and_replicate=False)
d.download(format = 'vorbis')
```

## Implementation

The main class is `audioset_download.Downloader`. It is initialized using the following parameters:
* `root_path`: the path to the directory where the dataset will be downloaded.
* `labels`: a list of labels to download. If `None`, all labels will be downloaded.
* `n_jobs`: the number of parallel downloads. Default is 1.
* `download_type`: the type of download. It can be one of the following:
  * `balanced_train`: balanced train set.
  * `unbalanced_train`: unbalanced train set. This is the default
  * `eval`: evaluation set.
* `copy_and_replicate`: if `True` if a file is associated to multiple labels, it will be copied and replicated for each label. If `False`, it will be associated to the first label in the list. Default is `True`.

The methods of the class are:
* `download(format='vorbis', quality=5)`: downloads the dataset. 
* The format can be one of the following (supported by [yt-dlp](https://github.com/yt-dlp/yt-dlp#post-processing-options) `--audio-format` parameter):
    * `vorbis`: downloads the dataset in Ogg Vorbis format. This is the default.
    * `wav`: downloads the dataset in WAV format.
    * `mp3`: downloads the dataset in MP3 format.
    * `m4a`: downloads the dataset in M4A format.
    * `flac`: downloads the dataset in FLAC format.
    * `opus`: downloads the dataset in Opus format.
    * `webm`: downloads the dataset in WebM format.
    * ... and many more.
  * The quality can be an integer between 0 and 10. Default is 5.
* `read_class_mapping()`: reads the class mapping file. It is not used externally.
* `download_file(...)`: downloads a single file. It is not used externally.