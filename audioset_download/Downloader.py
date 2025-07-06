import os
import joblib
import pandas as pd
import subprocess
import json

class Downloader:
    """
    This class implements the download of the AudioSet dataset.
    It only downloads the audio files according to the provided list of labels and associated timestamps.
    """

    def __init__(self, 
                    root_path: str,
                    labels: list = None, # None to download all the dataset
                    n_jobs: int = 1,
                    download_type: str = 'unbalanced_train',
                    copy_and_replicate: bool = True,
                    ):
        """
        This method initializes the class.
        :param root_path: root path of the dataset
        :param labels: list of labels to download
        :param n_jobs: number of parallel jobs
        :param download_type: type of download (unbalanced_train, balanced_train, eval)
        :param copy_and_replicate: if True, the audio file is copied and replicated for each label. 
                                    If False, the audio file is stored only once in the folder corresponding to the first label.
        """
        # Set the parameters
        self.root_path = root_path
        self.labels = labels
        self.n_jobs = n_jobs
        self.download_type = download_type
        self.copy_and_replicate = copy_and_replicate

        # Create the path
        os.makedirs(self.root_path, exist_ok=True)
        self.read_class_mapping()

    def read_class_mapping(self):
        """
        This method reads the class mapping.
        :return: class mapping
        """

        class_df = pd.read_csv(
            f"http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/class_labels_indices.csv", 
            sep=',',
        )

        self.display_to_machine_mapping = dict(zip(class_df['display_name'], class_df['mid']))
        self.machine_to_display_mapping = dict(zip(class_df['mid'], class_df['display_name']))
        return

    def get_audio_duration(self, file_path):
        """
        Get the duration of an audio file using ffprobe.
        :param file_path: path to the audio file
        :return: duration in seconds, or None if error
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'json', file_path
            ], capture_output=True, text=True, check=True)
            
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
        except (subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError):
            return None

    def download(
        self,
        format: str = 'vorbis',
        quality: int = 5,    
    ):
        """
        This method downloads the dataset using the provided parameters.
        :param format: format of the audio file (vorbis, mp3, m4a, wav), default is vorbis
        :param quality: quality of the audio file (0: best, 10: worst), default is 5
        """

        self.format = format
        self.quality = quality

        # Load the metadata
        metadata = pd.read_csv(
            f"http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/{self.download_type}_segments.csv", 
            sep=', ', 
            skiprows=3,
            header=None,
            names=['YTID', 'start_seconds', 'end_seconds', 'positive_labels'],
            engine='python'
        )
        if self.labels is not None:
            self.real_labels = [self.display_to_machine_mapping[label] for label in self.labels]
            metadata = metadata[metadata['positive_labels'].apply(lambda x: any([label in x for label in self.real_labels]))]
            # remove " in the labels
        metadata['positive_labels'] = metadata['positive_labels'].apply(lambda x: x.replace('"', ''))
        metadata = metadata.reset_index(drop=True)

        print(f'Downloading {len(metadata)} files...')

        # Download the dataset
        joblib.Parallel(n_jobs=self.n_jobs, verbose=10)(
            joblib.delayed(self.download_file)(metadata.loc[i, 'YTID'], metadata.loc[i, 'start_seconds'], metadata.loc[i, 'end_seconds'], metadata.loc[i, 'positive_labels']) for i in range(len(metadata))
        )

        print('Done.')

    def download_file(
            self, 
            ytid: str, 
            start_seconds: float,
            end_seconds: float,
            positive_labels: str,
        ):
        """
        This method downloads a single file. It only download the audio file at 16kHz.
        If a file is associated to multiple labels, it will be stored multiple times.
        :param ytid: YouTube ID.
        :param start_seconds: start time of the audio clip.
        :param end_seconds: end time of the audio clip.
        :param positive_labels: labels associated with the audio clip.
        """

        # Create the path for each label that is associated with the file
        if self.copy_and_replicate:
            for label in positive_labels.split(','):
                display_label = self.machine_to_display_mapping[label]
                os.makedirs(os.path.join(self.root_path, display_label), exist_ok=True)
        else:
            display_label = self.machine_to_display_mapping[positive_labels.split(',')[0]]
            os.makedirs(os.path.join(self.root_path, display_label), exist_ok=True)

        # Download the file using yt-dlp
        # store in the folder of the first label
        first_display_label = self.machine_to_display_mapping[positive_labels.split(',')[0]]
        
        # Determine file extension based on format
        if self.format == 'vorbis':
            ext = 'ogg'
        elif self.format == 'wav':
            ext = 'wav'
        elif self.format == 'mp3':
            ext = 'mp3'
        elif self.format == 'flac':
            ext = 'flac'
        elif self.format == 'opus':
            ext = 'opus'
        elif self.format == 'm4a':
            ext = 'm4a'
        else:
            ext = self.format
            
        file_path = os.path.join(self.root_path, first_display_label, f"{ytid}_{start_seconds}-{end_seconds}.{ext}")
        
        os.system(f'yt-dlp -x --audio-format {self.format} --audio-quality {self.quality} --output "{file_path}" --postprocessor-args "-ss {start_seconds} -to {end_seconds}" https://www.youtube.com/watch?v={ytid}')
        
        # Check if file was downloaded and has valid duration
        if os.path.exists(file_path):
            duration = self.get_audio_duration(file_path)
            if duration is None or duration <= 0.0:
                print(f"Removing file with invalid duration: {file_path}")
                os.remove(file_path)
                return
        else:
            print(f"File not downloaded: {file_path}")
            return
        
        if self.copy_and_replicate:
            # copy the file in the other folders
            for label in positive_labels.split(',')[1:]:
                display_label = self.machine_to_display_mapping[label]
                target_path = os.path.join(self.root_path, display_label, f"{ytid}_{start_seconds}-{end_seconds}.{ext}")
                os.system(f'cp "{file_path}" "{target_path}"')
        return

    def download_strong(
        self,
        root_path: str,
        format: str = 'vorbis',
        quality: int = 5,
        download_sets: list = ['train', 'eval']
    ):
        """
        Download the strong version of AudioSet dataset.
        :param root_path: path where to save the strong dataset
        :param format: audio format (vorbis, wav, mp3, etc.)
        :param quality: audio quality (0-10)
        :param download_sets: list of sets to download ('train', 'eval')
        """
        os.makedirs(root_path, exist_ok=True)
        
        self.format = format
        self.quality = quality
        
        # Determine file extension based on format
        if format == 'vorbis':
            ext = 'ogg'
        elif format == 'wav':
            ext = 'wav'
        elif format == 'mp3':
            ext = 'mp3'
        elif format == 'flac':
            ext = 'flac'
        elif format == 'opus':
            ext = 'opus'
        elif format == 'm4a':
            ext = 'm4a'
        else:
            ext = format
        
        for dataset_type in download_sets:
            print(f"Processing {dataset_type} set...")
            
            # Download and read the TSV file
            if dataset_type == 'train':
                url = "http://storage.googleapis.com/us_audioset/youtube_corpus/strong/audioset_train_strong.tsv"
            elif dataset_type == 'eval':
                url = "http://storage.googleapis.com/us_audioset/youtube_corpus/strong/audioset_eval_strong.tsv"
            else:
                raise ValueError(f"Unknown dataset type: {dataset_type}")
            
            # Read the strong dataset TSV
            strong_df = pd.read_csv(url, sep='\t')
            
            # Filter by labels if specified
            if self.labels is not None:
                real_labels = [self.display_to_machine_mapping[label] for label in self.labels]
                strong_df = strong_df[strong_df['label'].isin(real_labels)]
            
            if len(strong_df) == 0:
                print(f"No data found for {dataset_type} set with specified labels")
                continue
            
            print(f"Found {len(strong_df)} segments for {dataset_type} set")
            
            # Create audio directory
            audio_dir = os.path.join(root_path, f"{dataset_type}_audio")
            os.makedirs(audio_dir, exist_ok=True)
            
            # Group by segment_id to get unique segments with their timing info
            unique_segments = strong_df.groupby('segment_id').agg({
                'start_time_seconds': 'first',
                'end_time_seconds': 'first'
            }).reset_index()
            
            print(f"Downloading {len(unique_segments)} unique audio files...")
            
            # Download audio files
            joblib.Parallel(n_jobs=self.n_jobs, verbose=10)(
                joblib.delayed(self.download_strong_segment)(
                    row['segment_id'], 
                    row['start_time_seconds'], 
                    row['end_time_seconds'], 
                    audio_dir, 
                    ext
                ) for _, row in unique_segments.iterrows()
            )
            
            # Create the final TSV with path\tlabel_machine\tlabel format
            output_rows = []
            for _, row in strong_df.iterrows():
                segment_id = row['segment_id']
                label_machine = row['label']
                label_display = self.machine_to_display_mapping.get(label_machine, label_machine)
                
                # Check if audio file exists
                audio_path = os.path.join(audio_dir, f"{segment_id}.{ext}")
                if os.path.exists(audio_path):
                    # Use relative path from root_path
                    relative_path = os.path.relpath(audio_path, root_path)
                    output_rows.append([relative_path, label_machine, label_display])
            
            # Save the output TSV
            output_df = pd.DataFrame(output_rows, columns=['path', 'label_machine', 'label_display'])
            output_path = os.path.join(root_path, f"{dataset_type}_strong.tsv")
            output_df.to_csv(output_path, sep='\t', index=False)
            print(f"Saved {len(output_df)} entries to {output_path}")
        
        print("Strong dataset download completed!")

    def download_strong_segment(self, segment_id: str, start_seconds: float, end_seconds: float, audio_dir: str, ext: str):
        """
        Download a single segment for the strong dataset.
        :param segment_id: segment ID (format: YTID_SUFFIX)
        :param start_seconds: start time in seconds
        :param end_seconds: end time in seconds
        :param audio_dir: directory to save audio files
        :param ext: file extension
        """
        # Extract YTID from segment_id (everything before the first underscore)
        ytid = segment_id.split('_')[0]
        
        file_path = os.path.join(audio_dir, f"{segment_id}.{ext}")
        
        # Skip if file already exists
        if os.path.exists(file_path):
            return
        
        # Download using yt-dlp
        os.system(f'yt-dlp -x --audio-format {self.format} --audio-quality {self.quality} --output "{file_path}" --postprocessor-args "-ss {start_seconds} -to {end_seconds}" https://www.youtube.com/watch?v={ytid}')
        
        # Check if file was downloaded and has valid duration
        if os.path.exists(file_path):
            duration = self.get_audio_duration(file_path)
            if duration is None or duration <= 0.0:
                print(f"Removing file with invalid duration: {file_path}")
                os.remove(file_path)
                return
        else:
            print(f"File not downloaded: {file_path}")
            return