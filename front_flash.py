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
            pages = loader.load_and_split()
            return pages

    def split_chunks(sources, chunk_size):
        chunks = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_size / 10)
        for chunk in splitter.split_documents(sources):
            chunks.append(chunk)

        print(chunks)
        return chunks


    # Create Anki cards
    def create_anki_cards(pdf_text, chunk_size):

        divided_sections = split_chunks(pdf_text, chunk_size)
        print(divided_sections)
        # text = divided_sections[0]
        generated_flashcards = ' '
        for i, text in enumerate(divided_sections):

            ## You might need to change the Prompt to get consistent format. (Must do a bit of prompt engineering)
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": f"Create anki flashcards with the provided text using a format: question;answer next line question;answer etc. Keep question and the corresponding answer on the same line {text}"}
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

    generated_flashcards = create_anki_cards(pdf_text, chunk_size)

    return generated_flashcards

# Initialize OpenAI API with your key
openai.api_key = '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'
st.session_state.process_pdf = False

# Title (Must change the title)
st.markdown("<p style='font-size: 30px;'>Unleash the Power of GPT for Document Inquiries 📚</p>", unsafe_allow_html=True)


with st.sidebar:
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
        context = context_doc(st.session_state.pdf_docs_cached, chunk_size)
        print(context)

# Create a sidebar (must add icons
type = option_menu(None, ["FLASHCARDS", "DOWNLOAD", "TEACHER"],
                        icons=[],
                        menu_icon="cast", default_index=0, orientation="horizontal")

if type == "FLASHCARDS":

    #Add space
    st.write("")

    with st.expander('Options', expanded=True):

        def cards(question, answer):
            left_column.header(question)
            right_column.header(answer)


        left_column, right_column = st.columns([1, 1])
        st.session_state.question = "Here is my initial question"
        st.session_state.answer = "Here is my initial answer"
        # Initialize a session state variable
        if 'click_count' not in st.session_state:
            st.session_state.click_count = 0
            cards(st.session_state.question, st.session_state.answer)

        col1, col2, col3, col4, col5 = st.columns(5)

        # List of labels to toggle between
        labels = ["Edit", "Validate"]

        # Display a button that toggles between labels
        button_label = labels[st.session_state.click_count % 2]
        st.session_state.button_clicked = col3.button(button_label)

        # Update the session state on button click
        if st.session_state.button_clicked or not st.session_state.button_clicked:
            st.session_state.click_count += 1

        st.markdown(button_label)
        st.markdown(st.session_state.click_count)

        if button_label =="Validate":
            st.session_state.question = left_column.text_area("Edit your flashcard", value=st.session_state.question)
            st.session_state.answer = right_column.text_area("Edit your flashcard", value=st.session_state.answer)
            st.markdown(f"**Question:** {st.session_state.question}\n\n**Answer:** {st.session_state.answer}")
            question = left_column.text_area("Edit your flashcard", value="My text")
            # cards(st.session_state.question, st.session_state.answer)
        elif button_label =="Edit" and st.session_state.click_count!=1:
            cards(st.session_state.question, st.session_state.answer)


    if st.session_state.process_pdf:
        st.subheader("Your flashcards")


if type == "DOWNLOAD":
    st.button("Download your flashcards")
    # Call the function to write the file
    # Armand: I have it, but I just need to add it

    #This is the code:
    # # # Save the cards to a text file
    # with open("flashcards.txt", "w") as f:
    #     f.write(generated_flashcards)

if type =="TEACHER":

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
            st.session_state.messages.append({"role": "user", "content": prompt})
            print("in process")

            # Generate a response
            #Call the function which returns a list with the answer and the question

            with st.chat_message("assistant"):
                st.markdown(response[0])
                st.session_state.messages.append({"role": "assistant", "content": response[0]})

        else:
            with st.chat_message("assistant"):
                st.markdown("Please upload your file")

