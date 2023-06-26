import json

import openai
from prompts import multi_task_prompt
from render import (
    bot_msg_container_html_template,
    user_msg_container_html_template,
    render_article_preview,
    render_earnings_summary,
)
from charts import plot_prices
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_random
from utils import semantic_search, qna_with_discriminator, fetch_earnings_summaries

openai.api_key = st.secrets["OPENAI_API_KEY"]


@retry(wait=wait_random(min=1, max=2), stop=stop_after_attempt(3))
def intent_classifer(user_prompt):
    prompt = multi_task_prompt.replace("$PROMPT", user_prompt)
    response = openai.Completion.create(
        prompt=prompt, temperature=0, top_p=1, model="text-davinci-003", max_tokens=20
    )
    print(response.choices[0].text)
    intent = json.loads(response.choices[0].text)
    category_value = intent["category"]
    tickers_value = intent["tickers"]
    return category_value, tickers_value


def stock_question_handler(prompt, tickers_value):
    print("stock question handler")
    print(tickers_value)
    answer = qna_with_discriminator(prompt)
    figs = plot_prices(tickers_value)

    st.session_state.history.append(
        {
            "message": answer,
            "is_user": False,
            "figs": figs,
        }
    )

    figs = plot_prices(tickers_value)


def earnings_summary_handler(prompt, tickers_value):
    print("earnings summary handler")
    print(tickers_value)

    summaries = fetch_earnings_summaries(prompt, tickers_value)
    figs = plot_prices(tickers_value)

    for ticker, summary in summaries.items():
        if summary is not None:
            st.session_state.history.append(
                {
                    "message": render_earnings_summary(ticker, summary),
                    "is_user": False,
                    "figs": figs,
                }
            )
        else:
            st.session_state.history.append(
                {
                    "message": f"Sorry, I couldn't find an earnings summary for {ticker}",
                    "is_user": False,
                    "figs": figs,
                }
            )


def other_handler(prompt, tickers_value):
    print("other handler")
    print(tickers_value)

    response = openai.Completion.create(
        prompt=prompt,
        model="text-davinci-003",
        max_tokens=500,
    )
    bot_response = response["choices"][0]["text"]

    st.session_state.history.append(
        {
            "message": bot_response,
            "is_user": False,
        }
    )


def route_by_intent(prompt, category_value, tickers_value):
    if category_value == 1:
        return stock_question_handler(prompt, tickers_value)
    elif category_value == 2:
        return earnings_summary_handler(prompt, tickers_value)
    else:
        return other_handler(prompt, tickers_value)


st.title("Financial AI Assistant")

if "history" not in st.session_state:
    st.session_state.history = []


def generate_response():
    st.session_state.history.append(
        {
            "message": st.session_state.prompt,
            "is_user": True,
        }
    )

    category_value, tickers_value = intent_classifer(st.session_state.prompt)

    route_by_intent(st.session_state.prompt, category_value, tickers_value)


st.text_input(
    "Enter your prompt here:",
    key="prompt",
    placeholder="Why is Oscar's stock going up?",
    on_change=generate_response,
)

for message in st.session_state.history:
    if message["is_user"]:
        st.write(
            user_msg_container_html_template.replace("$MSG", message["message"]),
            unsafe_allow_html=True,
        )
    else:
        st.write(
            bot_msg_container_html_template.replace("$MSG", message["message"]),
            unsafe_allow_html=True,
        )

    if "figs" in message:
        for fig in message["figs"]:
            st.plotly_chart(fig, use_container_width=True)
