import os
import configparser
import pandas as pd
import time
import boto3
from multiprocessing import Pool

config = configparser.ConfigParser()
config.read("secrets/aws.txt")

secrets = {
            'key_id': config.get('secrets', 'key_id'),
            'access_key': config.get('secrets', 'access_key'),
        }
print(secrets['access_key'], secrets['key_id'])
# Configure the AWS credentials and services
transcribe = boto3.client('transcribe',
                          aws_access_key_id=secrets['key_id'],
                          aws_secret_access_key=secrets['access_key'],
                          region_name="ap-southeast-1"
)

translate = boto3.client(service_name='translate',
                         aws_access_key_id=secrets['key_id'],
                         aws_secret_access_key=secrets['access_key'],
                         region_name='ap-southeast-1',
                         use_ssl=True
)

# Function to perform Amazon Transcribe
def amazon_transcribe(audio_file_name, max_speakers=-1):
    try:
        if max_speakers > 10:
            raise ValueError("Maximum detected speakers is 10.")

        job_uri = "s3://audio-bucket-transcription/" + audio_file_name
        job_name = (audio_file_name.split('.')[0]).replace(" ", "")

        # Check if the name is taken or not
        job_name = check_job_name(job_name)

        if max_speakers != -1:
            transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': job_uri},
                MediaFormat='mp4',
                IdentifyMultipleLanguages=True,
                LanguageOptions=[
                    'en-IN', 'hi-IN', 'fa-IR'
                ],
                Settings={'ShowSpeakerLabels': True,
                          'MaxSpeakerLabels': max_speakers
                          }
            )
        else:
            transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': job_uri},
                MediaFormat='mp4',
                IdentifyMultipleLanguages=True,
                LanguageOptions=[
                    'en-IN', 'hi-IN', 'fa-IR'
                ],
                Settings={'ShowSpeakerLabels': True
                          }
            )

        while True:
            result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            if result['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            time.sleep(1)
        if result['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            data = pd.read_json(result['TranscriptionJob']['Transcript']['TranscriptFileUri'])
        return data
    except Exception as e:
        print(f"Error processing {audio_file_name}: {str(e)}")
        return None


def check_job_name(job_name):
    job_verification = True

    # all the transcriptions
    existed_jobs = transcribe.list_transcription_jobs()

    for job in existed_jobs['TranscriptionJobSummaries']:
        if job_name == job['TranscriptionJobName']:
            job_verification = False
            break

    if not job_verification:
        command = input(job_name + " has existed. \nDo you want to override the existed job (Y/N): ")
        if command.lower() == "y" or command.lower() == "yes":
            transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        elif command.lower() == "n" or command.lower() == "no":
            job_name = input("Insert new job name? ")
            check_job_name(job_name)
        else:
            print("Input can only be (Y/N)")
            command = input(job_name + " has existed. \nDo you want to override the existed job (Y/N): ")
    return job_name


# Function to perform translation
def translate_text(text, source_language_code, target_language_code):
    try:
        translated_result = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language_code,
            TargetLanguageCode=target_language_code
        )
        translated_text = translated_result.get('TranslatedText')
        return translated_text
    except Exception as e:
        print(f"Error translating text: {str(e)}")
        return None


# Create an empty DataFrame to store the data
data_list = []

# Process each audio file
def process_audio(audio_file):
    try:
        data = amazon_transcribe(audio_file, max_speakers=3)
        transcription = data['results']['transcripts'][0]['transcript']
        translated_text = translate_text(transcription, source_language_code="auto", target_language_code="en")

        filename = os.path.splitext(audio_file)[0]

        return {
            'Filename': filename,
            'Transcription': transcription,
            'TranslatedText': translated_text,
        }
    except Exception as e:
        print(f"Error processing {audio_file}: {str(e)}")
        return None

if __name__ == '__main__':
    # Directory containing the audio files
    audio_directory = 'data/Audio' # Change this to your own directory
    audio_files = os.listdir(audio_directory)

    pool = Pool(processes=3)  # Set the number of processes to 10 to handle 10 files at once
    data_list = pool.map(process_audio, audio_files)
    pool.close()
    pool.join()

    # Create a DataFrame from the list of data
    df = pd.DataFrame(data_list)

    # Save the DataFrame to a CSV file
    csv_file_path = 'AWS_Transcribing_Process_test.csv'
    df.to_csv(csv_file_path, index=False)

    print(f"Transcriptions and translations are saved to {csv_file_path}.")
