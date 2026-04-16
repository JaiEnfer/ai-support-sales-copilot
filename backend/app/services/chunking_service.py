from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
)


def split_text_into_chunks(text: str) -> list[str]:
    return splitter.split_text(text)
