"""
File Validator - Validação de arquivos de mídia
"""
import os


class FileValidator:
    """Validador de arquivos de mídia"""
    
    ALLOWED_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    MAX_FILE_SIZE_MB = 500
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    @classmethod
    def validate_extension(cls, filename: str) -> bool:
        """
        Valida extensão do arquivo
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            bool: True se válido
            
        Raises:
            ValueError: Se extensão inválida
        """
        if not filename:
            raise ValueError("Nome de arquivo é obrigatório")
        
        # Obter extensão
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Extensão de arquivo não permitida: {ext}. "
                f"Extensões permitidas: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )
        
        return True
    
    @classmethod
    def validate_file_size(cls, file_size_bytes: int) -> bool:
        """
        Valida tamanho do arquivo
        
        Args:
            file_size_bytes: Tamanho em bytes
            
        Returns:
            bool: True se válido
            
        Raises:
            ValueError: Se tamanho inválido
        """
        if file_size_bytes > cls.MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"Arquivo muito grande: {file_size_bytes / (1024*1024):.1f}MB. "
                f"Tamanho máximo permitido: {cls.MAX_FILE_SIZE_MB}MB"
            )
        
        return True
    
    @classmethod
    def validate_file_exists(cls, file_path: str) -> bool:
        """
        Valida se arquivo existe
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            bool: True se existe
            
        Raises:
            ValueError: Se arquivo não existe
        """
        if not os.path.exists(file_path):
            raise ValueError(f"Arquivo não encontrado: {file_path}")
        
        return True
    
    @classmethod
    def validate_media_file(cls, file_path: str, file_size_bytes: int = None) -> dict:
        """
        Valida arquivo de mídia completo
        
        Args:
            file_path: Caminho do arquivo
            file_size_bytes: Tamanho em bytes (opcional)
            
        Returns:
            Dict com informações do arquivo validado
            
        Raises:
            ValueError: Se arquivo inválido
        """
        # Validar extensão
        cls.validate_extension(file_path)
        
        # Validar se arquivo existe
        if file_path.startswith("http://") or file_path.startswith("https://"):
            # Arquivo remoto, não validar existência
            pass
        else:
            cls.validate_file_exists(file_path)
            
            # Validar tamanho se fornecido
            if file_size_bytes:
                cls.validate_file_size(file_size_bytes)
        
        # Obter extensão
        _, ext = os.path.splitext(file_path)
        
        return {
            "file_path": file_path,
            "extension": ext.lower(),
            "is_valid": True
        }
