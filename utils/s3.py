import boto3
import os


class S3:

    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str):
        """"""
        self.access_key = aws_access_key_id
        self.secret_key = aws_secret_access_key
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            aws_session_token=None
        )

    def upload_file(self, filepath: str, bucket: str = None, filename: str = None):
        """
        Upload a file to s3
        :param filepath: Where the file is located on the local machine
        :param filename: path to the file on s3
        :param bucket:
        :return:
        """
        filename = filename or filepath.split("/")[-1]
        self.client.upload_file(filepath, bucket, filename)

    def upload_directory(self, dir_path: str, bucket: str = None, dir_name: str = None):
        """
        Upload an entire directory to s3
        Todo[rotola]: Add option to zip the directory and upload once
        :param bucket:
        :param dir_path: Path to the local directory
        :return:
        """
        for path, subdirs, files in os.walk(dir_path):
            path = path.replace("\\", "/")
            directory_name = path.strip('./').lstrip("/")
            for file in files:
                self.upload_file(os.path.join(path, file), bucket, directory_name + '/' + file)


