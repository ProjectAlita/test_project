"""
Storage module for Docker Registry
"""

import hashlib
import json
import os
import shutil
import uuid
from typing import Dict, List, Optional, Tuple, BinaryIO

from flask import current_app


class Storage:
    """
    Storage class for Docker Registry
    Handles blobs, manifests, and uploads
    """

    def __init__(self, storage_path=None):
        """
        Initialize storage with path
        
        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = storage_path or current_app.config['STORAGE_PATH']
        
        # Ensure storage directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """
        Ensure all required directories exist
        """
        # Main storage directories
        for path in [
            self.storage_path,
            os.path.join(self.storage_path, 'blobs'),
            os.path.join(self.storage_path, 'manifests'),
            os.path.join(self.storage_path, 'uploads'),
            os.path.join(self.storage_path, 'repositories')
        ]:
            os.makedirs(path, exist_ok=True)
    
    def _get_repository_path(self, name: str) -> str:
        """
        Get path for repository
        
        Args:
            name: Repository name
            
        Returns:
            Repository path
        """
        return os.path.join(self.storage_path, 'repositories', name)
    
    def _get_blob_path(self, digest: str) -> str:
        """
        Get path for blob
        
        Args:
            digest: Blob digest
            
        Returns:
            Blob path
        """
        # Validate digest format
        if not digest.startswith('sha256:'):
            raise ValueError(f"Invalid digest format: {digest}")
            
        algorithm, hash_value = digest.split(':', 1)
        return os.path.join(self.storage_path, 'blobs', algorithm, hash_value[:2], hash_value)
    
    def _get_manifest_path(self, name: str, reference: str) -> str:
        """
        Get path for manifest
        
        Args:
            name: Repository name
            reference: Tag or digest
            
        Returns:
            Manifest path
        """
        if reference.startswith('sha256:'):
            algorithm, hash_value = reference.split(':', 1)
            return os.path.join(self.storage_path, 'manifests', name, algorithm, hash_value)
        else:
            return os.path.join(self.storage_path, 'manifests', name, 'tags', reference)
    
    def _get_upload_path(self, name: str, uuid: str) -> str:
        """
        Get path for upload
        
        Args:
            name: Repository name
            uuid: Upload UUID
            
        Returns:
            Upload path
        """
        return os.path.join(self.storage_path, 'uploads', name, uuid)
    
    def blob_exists(self, digest: str) -> bool:
        """
        Check if blob exists
        
        Args:
            digest: Blob digest
            
        Returns:
            True if blob exists
        """
        return os.path.exists(self._get_blob_path(digest))
    
    def get_blob(self, digest: str) -> Tuple[BinaryIO, int]:
        """
        Get blob data
        
        Args:
            digest: Blob digest
            
        Returns:
            Tuple of (file object, size)
        """
        path = self._get_blob_path(digest)
        if not os.path.exists(path):
            return None, 0
        
        size = os.path.getsize(path)
        return open(path, 'rb'), size
    
    def store_blob(self, data: bytes, digest: str = None) -> str:
        """
        Store blob data
        
        Args:
            data: Blob data
            digest: Expected digest
            
        Returns:
            Digest of stored blob
        """
        # Calculate digest if not provided
        if digest is None:
            digest = f"sha256:{hashlib.sha256(data).hexdigest()}"
        
        # Validate data matches digest if provided
        if digest.startswith('sha256:'):
            algorithm, hash_value = digest.split(':', 1)
            calculated_hash = hashlib.sha256(data).hexdigest()
            
            if hash_value != calculated_hash:
                raise ValueError(f"Data does not match digest: {digest} != sha256:{calculated_hash}")
        
        # Save blob
        path = self._get_blob_path(digest)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(data)
            
        return digest
    
    def delete_blob(self, digest: str) -> bool:
        """
        Delete blob
        
        Args:
            digest: Blob digest
            
        Returns:
            True if blob was deleted
        """
        path = self._get_blob_path(digest)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def manifest_exists(self, name: str, reference: str) -> bool:
        """
        Check if manifest exists
        
        Args:
            name: Repository name
            reference: Tag or digest
            
        Returns:
            True if manifest exists
        """
        return os.path.exists(self._get_manifest_path(name, reference))
    
    def get_manifest(self, name: str, reference: str) -> Tuple[Dict, str]:
        """
        Get manifest data
        
        Args:
            name: Repository name
            reference: Tag or digest
            
        Returns:
            Tuple of (manifest data, digest)
        """
        path = self._get_manifest_path(name, reference)
        if not os.path.exists(path):
            return None, None
        
        with open(path, 'rb') as f:
            data = f.read()
            manifest = json.loads(data)
            digest = f"sha256:{hashlib.sha256(data).hexdigest()}"
            
            return manifest, digest
    
    def store_manifest(self, name: str, reference: str, manifest_data: Dict) -> str:
        """
        Store manifest data
        
        Args:
            name: Repository name
            reference: Tag or digest
            manifest_data: Manifest data
            
        Returns:
            Digest of stored manifest
        """
        # Convert to bytes with canonical JSON encoding
        data = json.dumps(manifest_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        digest = f"sha256:{hashlib.sha256(data).hexdigest()}"
        
        # Save by digest
        digest_path = self._get_manifest_path(name, digest)
        os.makedirs(os.path.dirname(digest_path), exist_ok=True)
        
        with open(digest_path, 'wb') as f:
            f.write(data)
        
        # Save by tag if reference is not a digest
        if not reference.startswith('sha256:'):
            tag_path = self._get_manifest_path(name, reference)
            os.makedirs(os.path.dirname(tag_path), exist_ok=True)
            
            with open(tag_path, 'wb') as f:
                f.write(data)
        
        return digest
    
    def delete_manifest(self, name: str, reference: str) -> bool:
        """
        Delete manifest
        
        Args:
            name: Repository name
            reference: Tag or digest
            
        Returns:
            True if manifest was deleted
        """
        path = self._get_manifest_path(name, reference)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def init_upload(self, name: str) -> str:
        """
        Initialize upload session
        
        Args:
            name: Repository name
            
        Returns:
            Upload UUID
        """
        upload_id = str(uuid.uuid4())
        path = self._get_upload_path(name, upload_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb'):
            pass
            
        return upload_id
    
    def append_upload(self, name: str, upload_id: str, data: bytes, offset: int = None) -> int:
        """
        Append data to upload
        
        Args:
            name: Repository name
            upload_id: Upload ID
            data: Data to append
            offset: Expected offset
            
        Returns:
            New offset
        """
        path = self._get_upload_path(name, upload_id)
        if not os.path.exists(path):
            return -1
        
        size = os.path.getsize(path)
        if offset is not None and size != offset:
            return -1
        
        with open(path, 'ab') as f:
            f.write(data)
            
        return size + len(data)
    
    def complete_upload(self, name: str, upload_id: str, digest: str) -> str:
        """
        Complete upload and convert to blob
        
        Args:
            name: Repository name
            upload_id: Upload ID
            digest: Expected digest
            
        Returns:
            Digest of stored blob
        """
        upload_path = self._get_upload_path(name, upload_id)
        if not os.path.exists(upload_path):
            return None
        
        with open(upload_path, 'rb') as f:
            data = f.read()
        
        # Validate digest
        calculated_digest = f"sha256:{hashlib.sha256(data).hexdigest()}"
        if digest != calculated_digest:
            return None
        
        # Store as blob
        blob_path = self._get_blob_path(digest)
        os.makedirs(os.path.dirname(blob_path), exist_ok=True)
        
        shutil.move(upload_path, blob_path)
        
        # Remove upload directory if empty
        upload_dir = os.path.dirname(upload_path)
        if not os.listdir(upload_dir):
            os.rmdir(upload_dir)
            
        return digest
    
    def cancel_upload(self, name: str, upload_id: str) -> bool:
        """
        Cancel upload
        
        Args:
            name: Repository name
            upload_id: Upload ID
            
        Returns:
            True if upload was cancelled
        """
        path = self._get_upload_path(name, upload_id)
        if os.path.exists(path):
            os.remove(path)
            
            # Remove upload directory if empty
            upload_dir = os.path.dirname(path)
            if not os.listdir(upload_dir):
                os.rmdir(upload_dir)
                
            return True
        return False
    
    def list_repositories(self) -> List[str]:
        """
        List all repositories
        
        Returns:
            List of repository names
        """
        repositories = []
        
        manifests_dir = os.path.join(self.storage_path, 'manifests')
        if os.path.exists(manifests_dir):
            repositories = [name for name in os.listdir(manifests_dir) 
                           if os.path.isdir(os.path.join(manifests_dir, name))]
        
        return repositories
    
    def list_tags(self, name: str) -> List[str]:
        """
        List all tags for repository
        
        Args:
            name: Repository name
            
        Returns:
            List of tags
        """
        tags_path = os.path.join(self.storage_path, 'manifests', name, 'tags')
        if not os.path.exists(tags_path):
            return []
            
        return [tag for tag in os.listdir(tags_path) 
               if os.path.isfile(os.path.join(tags_path, tag))]