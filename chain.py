from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o",temperature=0)

prompt = ""


prompt_template = ChatPromptTemplate.from_template(prompt)
ai_chain = prompt_template | llm | StrOutputParser()
ai_response = ai_chain.invoke({"question": question,"documents": documents})