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

```python
from audioset_download import Downloader
d = Downloader(root_path='test', labels=None, n_jobs=2, download_type='unbalanced_train', copy_and_replicate=False)
d.download(format = 'vorbis')
```