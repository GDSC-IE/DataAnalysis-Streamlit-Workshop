# import required packages
import openai
from langchain.document_loaders import PyPDFLoader
import os
import tempfile
import streamlit as st
from streamlit_option_menu import option_menu
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Start by creating a venv:
# python -m venv myenv

# Activate your venv:
# source venv_name/bin/activate   (mac)
# venv_name\Scripts\activate  (windows)

# Run the code in the terminal:
# streamlit run front_flash.py

# Click on the link
# After each modification, simply refresh the page on your web browser

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


def context_doc(uploaded_docs, chunk_size):

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
            pages = loader.load_and_split()  # Why not pages.append(loader.load_and_split()) ?
        return pages

    def split_chunks(sources, chunk_size):
        chunks = []
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_size / 10)
        for chunk in splitter.split_documents(sources):
            chunks.append(chunk)

        return chunks

    # Create Anki cards
    def create_anki_cards(pdf_text, chunk_size):
        divided_sections = split_chunks(pdf_text, chunk_size)
        generated_flashcards = ''

        for i, text in enumerate(divided_sections):
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": f"Create {flashcard_number} different anki flashcards with the provided text using a format: question;answer next line question;answer etc. Keep question and the corresponding answer on the same line {text}"}
            ]

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3,
                max_tokens=2048
            )

            response_from_api = response['choices'][0]['message']['content']
            generated_flashcards += response_from_api

            return generated_flashcards

    pdf_text = read_pdf(uploaded_docs)

    generated_flashcards_anki = create_anki_cards(pdf_text, chunk_size)

    generated_flashcards_map = anki_flashcards_to_dict(
        generated_flashcards_anki)

    if 'edited_flashcards' not in st.session_state:
        st.session_state.edited_flashcards = generated_flashcards_map.copy()

    return generated_flashcards_anki, generated_flashcards_map


def anki_flashcards_to_dict(flashcards):
    flashcard_list = flashcards.split('\n')
    qa_dict = {}
    for card in flashcard_list:
        question, answer = card.split(';')
        qa_dict[question.strip()] = answer.strip()
    return qa_dict


st.session_state.process_pdf = False

# Title (Must change the title)
st.markdown("<p style='font-size: 30px;'>Unleash the Power of GPT for Document Inquiries 📚</p>",
            unsafe_allow_html=True)


with st.sidebar:
    # Set up OpenAI API key
    st.sidebar.header("OpenAI API")
    api_key = st.sidebar.text_input("Enter your OpenAI API key")
    # Initialize OpenAI API with your key
    openai.api_key = api_key

    # Set up the number of flashcards to generate
    st.sidebar.header("Number of Flashcards")
    flashcard_number = st.sidebar.number_input(
        "Number of flashcards to generate", min_value=1, max_value=10, value=5, step=1)

    # Set up a place to upload documents
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
        uploaded_docs = [file for file, keep in zip(
            st.session_state.uploaded_docs, keep_file_list) if keep]
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
            col2.markdown(
                '<p style="color:red; font-weight:bold;">No document</p>', unsafe_allow_html=True)
        elif process_pdf:
            st.session_state.process_pdf = True

    # Add a new if statement
    if st.session_state.process_pdf and st.session_state.pdf_docs_cached:
        context, flashcard_map = context_doc(
            st.session_state.pdf_docs_cached, chunk_size)

# Create a sidebar with option_menu
st.sidebar.header("Options")

selected_option = option_menu(None, ["FLASHCARDS", "DOWNLOAD", "TEACHER"], icons=[
], menu_icon="cast", orientation="horizontal")

# Initialize a session state variable to store the selected option
if selected_option == None:
    selected_option = "FLASHCARDS"  # Set the default option

if selected_option == "FLASHCARDS":
    # Add space
    st.write("")

    # Function to display and edit a box of question and answer
    def display_qna_box(q, a, index):
        st.subheader(f"#{index + 1}")
        question = st.text_area(
            label="Question", value=q, key=f"question_{index}")
        answer = st.text_area(
            label="Answer", value=a, key=f"answer_{index}")
        return question, answer

    if 'edited_flashcards' in st.session_state:
        # Display and edit all boxes
        for i, (question, answer) in enumerate(st.session_state.edited_flashcards.copy().items()):
            edited_q, edited_a = display_qna_box(question, answer, i)
            if edited_q != question or edited_a != answer:
                del st.session_state.edited_flashcards[question]
                st.session_state.edited_flashcards[edited_q] = edited_a

    # Update flashcards display
    # if st.session_state.process_pdf:
    #     st.subheader("Your flashcards")
    #     for idx, card in enumerate(context):
    #         st.text_area(f"Flashcard {idx+1}", value=card, height=100)

elif selected_option == "DOWNLOAD":
    st.button("Download your flashcards")
    print(st.session_state.edited_flashcards)
    # Call the function to write the file
    # Armand: I have it, but I just need to add it

    # This is the code:
    # # # Save the cards to a text file
    # with open("flashcards.txt", "w") as f:
    #     f.write(generated_flashcards)

elif selected_option == "TEACHER":
    # Clear the chat conversation when the button is clicked
    if st.button("Clear conversation"):
        st.session_state['messages'] = []

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat_input
    prompt = st.chat_input("What can I do for you?")

    # Process user input and respond using the selected language model
    if prompt:
        st.session_state.prompt_state = True
        st.session_state.prompt = prompt
    else:
        st.session_state.prompt_state = False

    if st.session_state.prompt_state:
        with st.chat_message("user"):
            st.markdown(st.session_state.prompt)

        if st.session_state.process:

            # Add user message to chat history
            st.session_state.messages.append(
                {"role": "user", "content": prompt})
            print("in process")

            # Generate a response
            # Call the function which returns a list with the answer and the question

            with st.chat_message("assistant"):
                st.markdown(response[0])
                st.session_state.messages.append(
                    {"role": "assistant", "content": response[0]})

        else:
            with st.chat_message("assistant"):
                st.markdown("Please upload your file")
