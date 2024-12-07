import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os
import time
import requests
from io import BytesIO
from bs4 import BeautifulSoup

# Function to set up page layout
def page_setup():
    st.header("Chat with different types of media/files and URLs!", anchor=False, divider="blue")

    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

# Function to allow users to select the media type
def get_typeofpdf():
    st.sidebar.header("Select type of Media", divider='orange')
    typepdf = st.sidebar.radio("Choose one:",
                               ("PDF files",
                                "Images",
                                "Video, mp4 file",
                                "Audio files",
                                "URL Link"))
    return typepdf

# Function to configure options for LLM model
def get_llminfo():
    st.sidebar.header("Options", divider='rainbow')
    tip1="Select a model you want to use."
    model = st.sidebar.radio("Choose LLM:",
                                  ("gemini-1.5-flash",
                                   "gemini-1.5-pro"),
                                  help=tip1)
    tip2="Lower temperatures are good for prompts that require a less open-ended or creative response, while higher temperatures can lead to more diverse or creative results. A temperature of 0 means that the highest probability tokens are always selected."
    temp = st.sidebar.slider("Temperature:", min_value=0.0,
                                    max_value=2.0, value=1.0, step=0.25, help=tip2)
    tip3="Used for nucleus sampling. Specify a lower value for less random responses and a higher value for more random responses."
    topp = st.sidebar.slider("Top P:", min_value=0.0,
                             max_value=1.0, value=0.94, step=0.01, help=tip3)
    tip4="Number of response tokens, 8194 is the limit."
    maxtokens = st.sidebar.slider("Maximum Tokens:", min_value=100,
                                  max_value=5000, value=2000, step=100, help=tip4)
    return model, temp, topp, maxtokens

# Function to download file from URL
def download_file_from_url(url):
    response = requests.get(url)
    return BytesIO(response.content)

# Function to scrape website content
def scrape_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract the text content from paragraphs or any other relevant tags
    text = ' '.join(p.text for p in soup.find_all('p'))
    return text

# Main function to run the app
def main():
    page_setup()
    typepdf = get_typeofpdf()
    model, temperature, top_p,  max_tokens = get_llminfo()

    if typepdf == "PDF files":
        uploaded_files = st.file_uploader("Choose 1 or more PDF", type='pdf', accept_multiple_files=True)
        if uploaded_files:
            text = ""
            for pdf in uploaded_files:
                pdf_reader = PdfReader(pdf)
                for page in pdf_reader.pages:
                    text += page.extract_text()

            generation_config = {
              "temperature": temperature,
              "top_p": top_p,
              "max_output_tokens": max_tokens,
              "response_mime_type": "text/plain",
              }
            model = genai.GenerativeModel(
              model_name=model,
              generation_config=generation_config,)

            question = st.text_input("Enter your question and hit return.")
            if question:
                response = model.generate_content([question, text])
                st.write(response.text)

    elif typepdf == "Images":
        image_file_name = st.file_uploader("Upload your image file.", type=["jpg", "jpeg", "png"])

        if image_file_name:
            # Determine mime type based on the file extension
            mime_type = None
            if image_file_name.name.endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            elif image_file_name.name.endswith('.png'):
                mime_type = 'image/png'
            
            # Upload image file with mime type
            image_file = genai.upload_file(path=image_file_name, mime_type=mime_type)

            if image_file:
                while image_file.state.name == "PROCESSING":
                    time.sleep(10)
                    image_file = genai.get_file(image_file.name)
                if image_file.state.name == "FAILED":
                    raise ValueError(image_file.state.name)

                prompt2 = st.text_input("Enter your prompt.")
                if prompt2:
                    generation_config = {
                      "temperature": temperature,
                      "top_p": top_p,
                      "max_output_tokens": max_tokens,}
                    model = genai.GenerativeModel(model_name=model, generation_config=generation_config,)
                    response = model.generate_content([image_file, prompt2],
                                                      request_options={"timeout": 600})
                    st.markdown(response.text)
                    genai.delete_file(image_file.name)

    elif typepdf == "Video, mp4 file":
        video_file_name = st.file_uploader("Upload your video", type=["mp4", "mov", "avi"])

        if video_file_name:
            # Determine mime type based on the file extension
            mime_type = None
            if video_file_name.name.endswith('.mp4'):
                mime_type = 'video/mp4'
            elif video_file_name.name.endswith('.mov'):
                mime_type = 'video/quicktime'
            elif video_file_name.name.endswith('.avi'):
                mime_type = 'video/x-msvideo'
            
            # Upload video file with mime type
            video_file = genai.upload_file(path=video_file_name, mime_type=mime_type)

            if video_file:
                while video_file.state.name == "PROCESSING":
                    time.sleep(10)
                    video_file = genai.get_file(video_file.name)
                if video_file.state.name == "FAILED":
                    raise ValueError(video_file.state.name)

                prompt3 = st.text_input("Enter your prompt.")  # Example: "What is said in this video in the first 20 seconds?"
                if prompt3:
                    model = genai.GenerativeModel(model_name=model)
                    st.write("Making LLM inference request...")
                    response = model.generate_content([video_file, prompt3],
                                                      request_options={"timeout": 600})
                    st.markdown(response.text)
                    genai.delete_file(video_file.name)

    elif typepdf == "Audio files":
        audio_file_name = st.file_uploader("Upload your audio", type=["mp3", "wav", "ogg"])

        if audio_file_name:
            # Determine mime type based on the file extension
            mime_type = None
            if audio_file_name.name.endswith('.mp3'):
                mime_type = 'audio/mpeg'
            elif audio_file_name.name.endswith('.wav'):
                mime_type = 'audio/wav'
            elif audio_file_name.name.endswith('.ogg'):
                mime_type = 'audio/ogg'
            
            # Upload audio file with mime type
            audio_file = genai.upload_file(path=audio_file_name, mime_type=mime_type)

            if audio_file:
                while audio_file.state.name == "PROCESSING":
                    time.sleep(10)
                    audio_file = genai.get_file(audio_file.name)
                if audio_file.state.name == "FAILED":
                    raise ValueError(audio_file.state.name)

                prompt3 = st.text_input("Enter your prompt.")  # Example: "What is said in this audio clip?"
                if prompt3:
                    model = genai.GenerativeModel(model_name=model)
                    response = model.generate_content([audio_file, prompt3],
                                                      request_options={"timeout": 600})
                    st.markdown(response.text)
                    genai.delete_file(audio_file.name)

    elif typepdf == "URL Link":
        url = st.text_input("Enter the URL of a website")
        if url:
            website_content = scrape_website(url)

            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_tokens,
                "response_mime_type": "text/plain",
            }
            model = genai.GenerativeModel(model_name=model, generation_config=generation_config,)
            
            prompt = st.text_input("Enter your question about the website content.")
            if prompt:
                response = model.generate_content([prompt, website_content])
                st.write(response.text)

if __name__ == '__main__':
    GEMINI_API_KEY = 'AIzaSyC7aKNc3ojDu8sBWeTz_c990Hpj-_rQnlc'
    genai.configure(api_key=GEMINI_API_KEY)
    main()
