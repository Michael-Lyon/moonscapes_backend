# myapp/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.conf import settings
from django.core.files.storage import default_storage
from .models import UploadedImage
from .serializers import UploadedImageSerializer
import requests
import logging
import os
import traceback
from django.core.files.base import ContentFile
from .models import FileUpload
from .serializers import FileUploadSerializer

import os
import subprocess
import base64
import aspose.threed as a3d



logger = logging.getLogger(__name__)

class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        print("HERE IN THE UPLOADED IMAGE METHOD")
        serializer = UploadedImageSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            image_url = request.build_absolute_uri(instance.image.url)

            logger.debug(f'Image URL: {image_url}')

            # Call 3D conversion API
            headers = {
                "Authorization": f"Bearer {settings.MESHY_API_KEY}"
            }
            payload = {
                "image_url": image_url,
                "enable_pbr": True,
            }

            logger.debug(f'Payload: {payload}')
            print(f'Payload: {payload}')

            try:
                response = requests.post("https://api.meshy.ai/v1/image-to-3d", headers=headers, json=payload)
                response.raise_for_status()
                task_id = response.json()["result"]

                # Save the task ID and initial status
                instance.task_id = task_id
                instance.status = 'processing'
                instance.save()

                # Provide the task ID to the client
                return Response({'task_id': task_id, 'status': 'processing', "model_urls":[]}, status=202)

            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 429:
                    logger.error('Too Many Requests: Rate limit exceeded.')
                    print('Too Many Requests: Rate limit exceeded.')
                    return Response({'error': 'Rate limit exceeded. Please try again later.'}, status=429)
                else:
                    logger.error(f'HTTP error occurred: {http_err}')
                    print(f'HTTP error occurred: {http_err}')
                    return Response({'error': 'Failed to process the image.'}, status=response.status_code)
            except Exception as err:
                logger.error(f'Other error occurred: {err}')
                print(f'Other error occurred: {err}')
                return Response({'error': 'An unexpected error occurred.'}, status=500)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=400)

class ImageStatusView(APIView):
    def get(self, request, task_id, *args, **kwargs):
        print("GET REQUEST IS HERE!!!")
        print(task_id)
        try:
            image = UploadedImage.objects.get(task_id=task_id)
        except UploadedImage.DoesNotExist:
            print("NOT FOUND")
            return Response({'error': 'Task ID not found'}, status=404)

        if image.status == "processing" or image.status == "completed":
        # if image.status == 'processing':
            headers = {
                "Authorization": f"Bearer {settings.MESHY_API_KEY}"
            }

            try:
                response = requests.get(f"https://api.meshy.ai/v1/image-to-3d/{task_id}", headers=headers)
                response.raise_for_status()
                model_data = response.json()
                image.model_data = model_data
                image.status = "completed"
                image.save()

                # Download model files and save them locally
                model_urls = model_data.get("model_urls", {})
                downloaded_files = {}

                for key, url in model_urls.items():
                    try:
                        file_response = requests.get(url)
                        if file_response.status_code == 200:
                            file_extension = url.split('.')[-1].split('?')[0]
                            file_name = f"{task_id}_{key}.{file_extension}"
                            if len(file_name) > 100:  # Ensure filename length is acceptable
                                file_name = f"{task_id}_{key}.{file_extension}"
                            file_path = default_storage.save(file_name, ContentFile(file_response.content))
                            downloaded_files[key] = request.build_absolute_uri(default_storage.url(file_path))
                    except Exception as e:
                        logger.error(f"Error downloading file {key} from {url}: {e}")
                        continue

                # Update model_data with local URLs
                model_data["model_urls"] = downloaded_files
                image.model_data = model_data
                image.save()

                return Response({'status': 'completed', 'model_urls': downloaded_files, "task_id": task_id}, status=200)

            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 429:
                    logger.error('Too Many Requests: Rate limit exceeded.')
                    print('Too Many Requests: Rate limit exceeded.')
                    return Response({'error': 'Rate limit exceeded. Please try again later.'}, status=429)
                elif response.status_code == 404:
                    logger.error('Task not yet complete.')
                    print('Task not yet complete.')
                    return Response({'status': 'processing'}, status=202)
                else:
                    logger.error(f'HTTP error occurred: {http_err}')
                    print(f'HTTP error occurred: {http_err}')
                    return Response({'error': 'Failed to retrieve the model data.'}, status=response.status_code)
            except Exception as err:
                traceback.print_exc()
                logger.error(f'Other error occurred: {err}')
                print(f'Other error occurred: {err}')
                return Response({'error': 'An unexpected error occurred.'}, status=500)
        else:
            print(image.__dict__)
            return Response({'status': image.status, 'model_urls': image.model_data.get("model_urls", {}), "task_id": image.task_id})



class UploadFileView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data

        try:
            # Decode base64 data
            usdz_file_data = data.get("usdzBase64")
            json_file_data = data.get("jsonBase64")
            thumbnail_file_data = data.get("thumbnailBase64")

            if not usdz_file_data or not json_file_data or not thumbnail_file_data:
                return Response({"error": "Missing file data"}, status=status.HTTP_400_BAD_REQUEST)

            # Decode base64-encoded strings to binary data
            usdz_file_content = base64.b64decode(usdz_file_data)
            json_file_content = base64.b64decode(json_file_data)
            thumbnail_file_content = base64.b64decode(thumbnail_file_data)

            # Generate random filenames
            usdz_file_name = f"Room_{self._generate_random_name()}.usdz"
            json_file_name = f"Room_{self._generate_random_name()}.json"
            thumbnail_file_name = f"RoomThumbnail_{self._generate_random_name()}.png"
            glb_file_name = f"Room_{self._generate_random_name()}.glb"

            # Define paths to save files
            usdz_file_path = self.ensure_directory_exists('uploads/usdz/', usdz_file_name)
            json_file_path = self.ensure_directory_exists('uploads/json/', json_file_name)
            thumbnail_file_path = self.ensure_directory_exists('uploads/thumbnails/', thumbnail_file_name)
            glb_file_path = self.ensure_directory_exists('uploads/glb/', glb_file_name)

            # Save USDZ file
            with open(usdz_file_path, 'wb') as usdz_file:
                usdz_file.write(usdz_file_content)

            # Save JSON file
            with open(json_file_path, 'wb') as json_file:
                json_file.write(json_file_content)

            # Save Thumbnail file
            with open(thumbnail_file_path, 'wb') as thumbnail_file:
                thumbnail_file.write(thumbnail_file_content)

            # Convert USDZ to GLB using Aspose.3D
            self.convert_usdz_to_glb(usdz_file_path, glb_file_path)

            # Save the files to the model
            file_upload = FileUpload.objects.create(
                usdz_file=ContentFile(usdz_file_content, usdz_file_name),
                glb_file=ContentFile(open(glb_file_path, 'rb').read(), glb_file_name),
                json_file=ContentFile(json_file_content, json_file_name),
                thumbnail=ContentFile(thumbnail_file_content, thumbnail_file_name)
            )

            # Get the URLs of the saved files
            usdz_file_url = request.build_absolute_uri(file_upload.usdz_file.url)
            glb_file_url = request.build_absolute_uri(file_upload.glb_file.url)
            thumbnail_url = request.build_absolute_uri(file_upload.thumbnail.url)

            data = {
                "usdz_url": usdz_file_url,
                "glb_url": glb_file_url,
                "thumbnail_url": thumbnail_url,
            }
            print(data)
            return Response(data, status=status.HTTP_201_CREATED)

        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Generate random name for files
    def _generate_random_name(self):
        import uuid
        return uuid.uuid4().hex

    # Function to convert USDZ to GLB using Aspose.3D
    def convert_usdz_to_glb(self, usdz_path, glb_path):
        try:
            # Load the USDZ file via Aspose.3D
            scene = a3d.Scene.from_file(usdz_path)
            # Save the scene as GLB format
            scene.save(glb_path)
        except Exception as e:
            print(f"Error converting USDZ to GLB: {e}")
            raise

    # Ensure the directory exists, if not, create it
    def ensure_directory_exists(self, relative_path, filename):
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return os.path.join(full_path, filename)