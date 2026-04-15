"""
知识库
"""

import hashlib
import os
from datetime import datetime

import config_data as config
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from model_factory import build_embedding


def check_md5(md5_str: str) -> bool:
    """
    检查传入的 md5 是否已经被处理过
    return:
        False -> 未处理过
        True  -> 已处理过
    """
    if not os.path.exists(config.md5_path):
        open(config.md5_path, "w", encoding="utf-8").close()
        return False

    with open(config.md5_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if line.strip() == md5_str:
                return True

    return False


def save_md5(md5_str: str) -> None:
    """将 md5 记录到文件中"""
    with open(config.md5_path, "a", encoding="utf-8") as f:
        f.write(md5_str + "\n")


def get_string_md5(input_str: str, encoding: str = "utf-8") -> str:
    """将字符串转换成 md5"""
    str_bytes = input_str.encode(encoding=encoding)
    md5_obj = hashlib.md5()
    md5_obj.update(str_bytes)
    return md5_obj.hexdigest()


class KnowledgeBaseService(object):
    def __init__(self):
        os.makedirs(config.persist_directory, exist_ok=True)

        self.chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=build_embedding(),
            persist_directory=config.persist_directory,
        )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=len,
        )

    def upload_by_str(self, data: str, filename: str) -> str:
        """将字符串向量化后写入知识库"""
        data = (data or "").strip()
        if not data:
            return "[失败] 文件内容为空，未写入知识库"

        md5_hex = get_string_md5(data)
        if check_md5(md5_hex):
            return "[跳过] 内容已经存在知识库中"

        if len(data) > config.max_split_char_number:
            knowledge_chunks = self.splitter.split_text(data)
        else:
            knowledge_chunks = [data]

        if not knowledge_chunks:
            return "[失败] 文本切分后为空，未写入知识库"

        metadata = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": config.operator,
        }

        self.chroma.add_texts(
            texts=knowledge_chunks,
            metadatas=[metadata.copy() for _ in knowledge_chunks],
        )

        save_md5(md5_hex)

        return f"[成功] 内容已经成功载入向量库，共写入 {len(knowledge_chunks)} 个文本片段"


if __name__ == "__main__":
    service = KnowledgeBaseService()
    result = service.upload_by_str("周杰伦是华语流行歌手。", "test.txt")
    print(result)