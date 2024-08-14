import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import pandas as pd
import docx
from PyPDF2 import PdfReader
import json
import typing_extensions

# Load environment variables
load_dotenv()

# Configure the Google Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel(model_name="gemini-1.5-pro")
chat = model.start_chat(history=[])

# Initialize models for pandas commands and natural language responses
model_pandas = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction="You are an expert python developer who works with pandas. You make sure to generate simple pandas 'command' for the user queries in JSON format. No need to add 'print' function. Analyze the datatypes of the columns before generating the command. If unfeasible, return 'None'.")
model_response = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction="Your task is to comprehend. You must analyze the user query and response data to generate a response in natural language.")

# Response Schema for pandas commands
class Command(typing_extensions.TypedDict):
    command: str

# Function to get responses from Google Gemini
def get_gemini_response(question):
    response = chat.send_message(question, stream=True)
    return response

# Function to handle file uploads and generate the appropriate query context
def handle_file_question(uploaded_file, question):
    file_extension = uploaded_file.name.split(".")[-1].lower()

    if file_extension in ['jpeg', 'jpg', 'png']:
        image = Image.open(uploaded_file)
        st.image(image=image, caption="Uploaded Image", use_column_width=True)
        question = [question, image]
        return question

    elif file_extension == 'docx':
        doc = docx.Document(uploaded_file)
        full_txt = []
        for i in doc.paragraphs:
            full_txt.append(i.text)
        return question + '\nText:' + '\n'.join(full_txt)

    elif file_extension == 'txt':
        content = uploaded_file.read().decode('utf-8')
        return question + '\nText:' + content

    elif file_extension == 'csv':
        df = pd.read_csv(uploaded_file)
        head = str(df.head().to_dict())
        desc = str(df.describe().to_dict())
        cols = str(df.columns.to_list())
        dtype = str(df.dtypes.to_dict())
        final_query = f"The dataframe name is 'df'. df has the columns {cols} and their datatypes are {dtype}. df is in the following format: {desc}. The head of df is: {head}. You cannot use df.info() or any command that cannot be printed. Write a pandas command for this query on the dataframe df: {question}"
        return final_query, df

    else:
        pdf_reader = PdfReader(uploaded_file)
        text = ''
        for i in pdf_reader.pages:
            text += i.extract_text()
        return question + '\nText:' + text

# Streamlit UI configuration
st.set_page_config(page_title="Chat App")
st.header("Chat With Your Data")

uploaded_file = st.file_uploader("Choose a file...", type=['jpeg', 'jpg', 'png', 'pdf', 'txt', 'docx', 'csv'])
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input()
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

file_final = None
df = None

if uploaded_file and user_query:
    if uploaded_file.name.split(".")[-1].lower() == 'csv':
        file_final, df = handle_file_question(uploaded_file, user_query)
    else:
        file_final = handle_file_question(uploaded_file, user_query)
else:
    file_final = user_query

# Process the final query with the appropriate model
if file_final:
    if uploaded_file and uploaded_file.name.split(".")[-1].lower() == 'csv' and df is not None:
        # Handle CSV files with pandas command generation
        with st.spinner('Analyzing the data...'):
            response = model_pandas.generate_content(
                file_final,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=Command,
                    temperature=0.3
                )
            )

            command = json.loads(response.text).get('command')
            print(command)
            
            if command:
                try:
                    # Safely evaluate the command
                    exec(f"data = {command}")
                    natural_response = f"The user query is {user_query}. The output of the command is {str(data)}. If the data is 'None', you can say 'Please ask a query to get started'. Do not mention the command used. Generate a response in natural language for the output."
                    bot_response = model_response.generate_content(
                        natural_response,
                        generation_config=genai.GenerationConfig(temperature=0.7)
                    )
                    st.chat_message("assistant").write(bot_response.text)
                    st.session_state.messages.append({"role": "assistant", "content": bot_response.text})

                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"Error executing the command: {str(e)}"})
                    st.chat_message("assistant").write(f"Error executing the command: {str(e)}")

            else:
                st.session_state.messages.append({"role": "assistant", "content": "Could not generate a valid pandas command."})
                st.chat_message("assistant").write("Could not generate a valid pandas command.")

    else:
        # Handle other types of files and queries
        response = get_gemini_response(file_final)
        st.chat_message("assistant").write(' '.join(chunk.text for chunk in response))
        st.session_state.messages.append({"role": "assistant", "content": ' '.join(chunk.text for chunk in response)})