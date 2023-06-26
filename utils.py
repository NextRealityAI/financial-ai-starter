import openai
import streamlit as st
import requests
from prompts import relevance_prompt, stock_question_template

openai.api_key = st.secrets["OPENAI_API_KEY"]


def get_embeddings_openai(text):
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    response = response["data"]
    # extract embeddings from responses
    return [x["embedding"] for x in response]


def semantic_search(query, **kwargs):
    xq = get_embeddings_openai(query)

    url = st.secrets["PINECONE_URL"]
    headers = {
        "Api-Key": st.secrets["PINECONE_API_KEY"],
        "Content-Type": "application/json",
    }
    body = {
        "vector": xq[0],
        "topK": str(kwargs["top_k"]) if "top_k" in kwargs else "1",
        "includeMetadata": "false"
        if "include_metadata" in kwargs and not kwargs["include_metadata"]
        else "true",
        "namespace": kwargs["namespace"] if "namespace" in kwargs else "",
        "filter": kwargs["filter"] if "filter" in kwargs else "",
    }
    try:
        res = requests.post(url, json=body, headers=headers)
        res = res.json()
        titles = [r["metadata"]["title"] for r in res["matches"]]
        previews = [r["metadata"]["text"] for r in res["matches"]]
        url = [r["metadata"]["url"] for r in res["matches"]]
        return list(zip(titles, url, previews))
    except Exception as e:
        print("e")
        return None


# put the above in a function
def get_probs(res):
    print(res)
    logprobs = res["choices"][0]["logprobs"]["top_logprobs"][0]
    probs = {k: 2.718**v for k, v in logprobs.items()}
    return probs


def qna_with_discriminator(query, threshold=0.7, debug=True):
    prompt = query
    articles = semantic_search(query)  # replace with semantic_search for our app
    context = "\r".join([x[2] for x in articles])

    # invoke discriminator
    model = "text-embedding-ada-002"
    res = openai.Completion.create(
        model=model,
        prompt=relevance_prompt.replace("$CONTEXT", context).replace(
            "$QUESTION", query
        ),
        max_tokens=1,
        temperature=0,
        logprobs=2,
    )

    yes_prob = get_probs(res)  # this is our yes probability
    print(yes_prob)

    if debug:
        print(yes_prob)

        # if "Yes" in yes_prob and float(yes_prob["Yes"]) > threshold:
        # answer
        prompt = stock_question_template.replace("$CONTEXT", context).replace(
            "$QUESTION", query
        )
        if debug:
            print(prompt)
            # we set the temp to 0 to increase reproducability
        res = openai.Completion.create(
            prompt=prompt,
            temperature=0,
            top_p=1,
            model="text-davinci-003",
            max_tokens=256,
        )
        return res["choices"][0]["text"]
    else:
        return "I don't know because I don't have the context."


def fetch_earnings_summaries(prompt, tickers_value):
    summaries = {}
    for ticker in tickers_value:
        matches = semantic_search(
            prompt,
            filter={"ticker": {"$eq": ticker}},
            top_k=1,
            namespace="earnings_summary",
            include_metadata=True,
        )

        print(matches)

        if matches is not None and len(matches) > 0:
            summaries[ticker] = {}
            summaries[ticker]["summary"] = matches[0][2]
            summaries[ticker]["transcript_title"] = matches[0][0]
        else:
            summaries[ticker] = None

    return summaries
