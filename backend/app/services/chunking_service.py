from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text_into_chunks(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )
    return splitter.split_text(text)