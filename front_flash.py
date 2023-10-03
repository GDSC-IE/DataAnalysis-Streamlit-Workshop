# import required packages
import openai
from langchain.document_loaders import PyPDFLoader
import os
import tempfile
import streamlit as st
from streamlit_option_menu import option_menu
from langchain.text_splitter import RecursiveCharacterTextSplitter


#Start by creating a venv:
# python -m venv myenv

#Activate your venv:
# source venv_name/bin/activate   (mac)
# venv_name\Scripts\activate  (windows)

# Run the code in the terminal:
# streamlit run front_flash.py

# Click on the link
# After each modification, simply refresh the page on your web browser


#Armand's api key: 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


def get_file_icon(file_extension):
    # Replace this with the appropriate icons for different file types
    icon_mapping = {
        ".txt": "📄",
        ".csv": "📄",
        ".png": "🖼️",
        ".jpg": "🖼️",
        ".jpeg": "🖼️",
        ".pdf": "📄",
        ".eml": "📨"
        # Add more file types and their corresponding icons as needed
    }
    return icon_mapping.get(file_extension, "📄")

def caching(caching_docs):
    return caching_docs

def context_doc(uploaded_docs, chunk_size, flashcard_number):

    def read_pdf(pdf_docs):
        temp_dir = tempfile.TemporaryDirectory()
        pdf_paths = []
        for pdf_doc in pdf_docs:
            pdf_path = os.path.join(temp_dir.name, pdf_doc.name)
            with open(pdf_path, "wb") as f:
                f.write(pdf_doc.getbuffer())
            pdf_paths.append(pdf_path)
        for pdf_path in pdf_paths:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load_and_split()
            return pages

    def split_chunks(sources, chunk_size):
        chunks = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_size / 10)
        for chunk in splitter.split_documents(sources):
            chunks.append(chunk)

        print(chunks)
        return chunks

    def extract_clear_text(text):
        # Remove page numbers
        text = re.sub(r'\n\d+\s', '\n', text)

        # Remove unwanted characters and multiple spaces
        text = re.sub(r'[^\w\s.]', '', text)
        text = re.sub(r'\s+', ' ', text)

        # Remove trailing and leading spaces
        text = text.strip()

        return text


    # Create Anki cards
    def create_anki_cards(content, chunk_size):

        divided_sections = split_chunks(content, chunk_size)

        # text = divided_sections[0]
        generated_flashcards = ' '
        for i, text in enumerate(divided_sections):

            ## You might need to change the Prompt to get consistent format. (Must do a bit of prompt engineering)
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": f"Create {flashcard_number} anki flashcards with the provided text using a format: question;answer next line question;answer etc. Keep question and the corresponding answer on the same line. For each question you should mention the concept or topic related. {text}"}
            ]

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,
                max_tokens=2048 #Defines the limit of token per search
            )

            response_from_api = response['choices'][0]['message']['content']  # .strip()
            generated_flashcards += response_from_api

        return generated_flashcards


    pdf_text = read_pdf(uploaded_docs)

    clear_pdf = extract_clear_text(pdf_text)

    generated_flashcards = create_anki_cards(pdf_text, chunk_size)

    return generated_flashcards

# Initialize OpenAI API with your key
openai.api_key = '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'
st.session_state.process_pdf = False

# Title (Must change the title)
st.markdown("<p style='font-size: 30px;'>Unleash the Power of GPT for Document Inquiries 📚</p>", unsafe_allow_html=True)


with st.sidebar:

    # Set up OpenAI API key
    st.sidebar.header("OpenAI API")
    api_key = st.sidebar.text_input("Enter your OpenAI API key")
    # Initialize OpenAI API with your key
    openai.api_key = api_key

    # Set up the number of flashcards to generate
    st.sidebar.header("Number of Flashcards")
    st.session_state.flashcard_number = st.sidebar.number_input(
        "Number of flashcards to generate", min_value=1, max_value=15, value=5, step=1)

    st.subheader("Your documents")
    st.session_state.uploaded_docs = st.file_uploader(
        "Upload your PDFs here and click on 'Process'", accept_multiple_files=True, type=["pdf"])

    keep_file_list = []
    if st.session_state.uploaded_docs:
        # Hide the default file uploader messages
        st.markdown('''
                <style>
                    .uploadedFile {display: none}
                <style>''',
                    unsafe_allow_html=True)

        # Display checkboxes to select PDFs for processing
        for uploaded_file in st.session_state.uploaded_docs:
            file_name = uploaded_file.name
            file_size = len(uploaded_file.getvalue())
            file_extension = os.path.splitext(file_name)[1]

            keep_file = st.checkbox(f"{file_name} ({get_file_icon(file_extension)}) - {file_size} bytes",
                                    value=True)
            keep_file_list.append(keep_file)

        # Cache selected PDFs
        uploaded_docs = [file for file, keep in zip(st.session_state.uploaded_docs, keep_file_list) if keep]
        uploaded_docs_cached = caching(uploaded_docs)
        st.session_state.pdf_docs_cached = uploaded_docs_cached

        # Set the chunk size for document processing
        chunk_size = st.slider('Chunk size:',
                               min_value=500,
                               max_value=4500,
                               step=100)

        col1, col2 = st.columns([1, 2])
        process_pdf = col1.button("Process")
        if process_pdf and not st.session_state.uploaded_docs:
            col2.markdown('<p style="color:red; font-weight:bold;">No document</p>', unsafe_allow_html=True)
        elif process_pdf:
            st.session_state.process_pdf = True


    #Add a new if statement
    if st.session_state.process_pdf and st.session_state.pdf_docs_cached:
        st.session_state.context = context_doc(st.session_state.pdf_docs_cached, chunk_size, st.session_state.flashcard_number)

# Create a sidebar (must add icons
type = option_menu(None, ["FLASHCARDS", "DOWNLOAD"],
                        icons=[],
                        menu_icon="cast", default_index=0, orientation="horizontal")

if type == "FLASHCARDS":
    #Add space
    st.write("")

    if "context" not in st.session_state:
        st.subheader(f"Generate first your flashcards")
    else:
        # Function to display and edit a box of question and answer
        def display_qna_box(q, a, index):
            st.subheader(f"#{index + 1}")
            question = st.text_area(
                label="Question", value=q, key=f"question_{index}")
            answer = st.text_area(
                label="Answer", value=a, key=f"answer_{index}")
            return question, answer

        if "edited_flashcards" not in st.session_state:
            st.session_state.edited_flashcards = {
                "What is 2 + 2?": "4",
                "What is the capital of France?": "Paris",
                "What is the largest planet in our solar system?": "Jupiter"
            }

        if 'edited_flashcards' in st.session_state:
            # Display and edit all boxes
            for i, (question, answer) in enumerate(st.session_state.edited_flashcards.copy().items()):
                edited_q, edited_a = display_qna_box(question, answer, i)
                if edited_q != question or edited_a != answer:
                    del st.session_state.edited_flashcards[question]
                    st.session_state.edited_flashcards[edited_q] = edited_a


if type == "DOWNLOAD":

    if "string_edited_flashcards" not in st.session_state:
        st.session_state.string_edited_flashcards = ""

    # Transform the dictionary into a list of key-value pairs and iterate through it
    for key, value in st.session_state.edited_flashcards.items():
        st.session_state.string_edited_flashcards += ', '.join([f"{key}: {value}"])
        st.session_state.string_edited_flashcards += "\n"

    if ':' in st.session_state.string_edited_flashcards:
        st.session_state.string_edited_flashcards = st.session_state.string_edited_flashcards.replace(':', ';')

    #Initialize for the moment
    st.download_button('Download Flashcards', st.session_state.string_edited_flashcards, 'my_flashcards.txt')


