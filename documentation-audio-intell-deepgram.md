***

title: Getting Started
subtitle: >-
An introduction to using Deepgram's audio intelligence features to analyze
audio using Deepgram SDKs.
slug: docs/audio-intelligence
-----------------------------

<Card href="https://playground.deepgram.com/?endpoint=listen&summarize=v2&topics=true&intents=true&smart_format=true&sentiment=true&language=en&model=nova-3">
  <div class="t-default text-base font-semibold">Deepgram API Playground</div>
  Try this feature out in our API Playground.
</Card>

<br />

In this guide, you'll learn how to analyze audio using Deepgram's intelligence features: Summarization, Topic Detection, Intent Recognition, and Sentiment Analysis. The code examples use [Deepgram's SDKs](/home).

<Info>
  Before you start, you'll need to follow the steps in the [Make Your First API Request](/guides/fundamentals/make-your-first-api-request) guide to obtain a Deepgram API key, and configure your environment if you are choosing to use a Deepgram SDK.
</Info>

## Purpose

Audio Intelligence transcribes audio files and performs four types of analysis on the transcript content: [Summarization](/docs/summarization), [Topic Detection](/docs/topic-detection), [Intent Recognition](/docs/intent-recognition), and [Sentiment Analysis](/docs/sentiment-analysis). You can send audio as a local file or hosted URL to receive transcription and structured analysis results.

## Make the Request

A request made using one of the audio intelligence features will follow the same form for each of the features; therefore, this guide will walk you through how to make one request, and you can use the feature(s) of your choice depending on which feature you want to use (Summarization, Topic Detection, Intent Recognition, or Sentiment Analysis).

### Choose Your Audio Source

An audio source can be sent to Deepgram as an audio file or as a url of a hosted audio file. These are referred to as a **local file request** or a **remote file request** (which is a hosted url such as `https://YOUR_FILE_URL.txt`).

### Local File Request

This example shows how to analyze a **local audio file** as your audio source.

<CodeGroup>
  ```javascript JavaScript
  const { createClient } = require("@deepgram/sdk");
  const fs = require("fs");

  const transcribeFile = async () => {
    // STEP 1: Create a Deepgram client using the API key
    const deepgram = createClient(process.env.DEEPGRAM_API_KEY);

    // STEP 2: Call the transcribeFile method with the audio payload and options
    const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
      fs.readFileSync("callcenter.wav"),
      // STEP 3: Configure Deepgram options for audio analysis
      {
        model: "nova-3",
        sentiment: true,
        // intents: true,
        // summarize: "v2",
        // topics: true,
      }
    );

    if (error) throw error;
    // STEP 4: Print the results
    if (!error) console.dir(result, { depth: null });
  };

  transcribeFile();
  ```

  ```python Python
  # For help migrating to the new Python SDK, check out our migration guide:
  # https://github.com/deepgram/deepgram-python-sdk/blob/main/docs/Migrating-v3-to-v5.md

  import os
  from dotenv import load_dotenv

  from deepgram import (
      DeepgramClient,
  )

  load_dotenv()

  # Path to the audio file
  AUDIO_FILE = "callcenter.wav"

  API_KEY = os.getenv("DEEPGRAM_API_KEY")

  def main():
      try:
          # STEP 1 Create a Deepgram client using the API key
          deepgram = DeepgramClient(api_key=API_KEY)

          with open(AUDIO_FILE, "rb") as file:
              buffer_data = file.read()

          # STEP 2: Call the transcribe_file method with the audio file and options
          response = deepgram.listen.v1.media.transcribe_file(
              request=buffer_data,
              model="nova-2",
              sentiment=True,
              # intents=True,
              # summarize="v2",
              # topics=True,
          )

          # STEP 4: Print the response
          print(response.to_json(indent=4))

      except Exception as e:
          print(f"Exception: {e}")

  if __name__ == "__main__":
      main()
  ```

  ```go Go
  package main

  import (
  	"context"
  	"encoding/json"
  	"fmt"
  	"os"

  	prettyjson "github.com/hokaccha/go-prettyjson"

  	prerecorded "github.com/deepgram/deepgram-go-sdk/pkg/api/prerecorded/v1"
  	interfaces "github.com/deepgram/deepgram-go-sdk/pkg/client/interfaces"
  	client "github.com/deepgram/deepgram-go-sdk/pkg/client/prerecorded"
  )

  // path to the audio file to analyze
  const (
  	filePath string = "./callcenter.wav"
  )

  func main() {
  	// STEP 1: init Deepgram client library
  	client.InitWithDefault()

  	// STEP 2: define context to manage the lifecycle of the request
  	ctx := context.Background()

  	// STEP 3: define options for the request
  	options := interfaces.PreRecordedTranscriptionOptions{
  		Model:     "nova-2",
  		Sentiment: true,
  		// Summarize: "v2",
  		// Topics: true,
  		// Intents:  true,
  	}

  	// STEP 4: create a Deepgram client using default settings
  	// NOTE: you can set your API KEY in your bash profile by typing the following line in your shell:
  	// export DEEPGRAM_API_KEY = "YOUR_DEEPGRAM_API_KEY"
  	c := client.NewWithDefaults()
  	dg := prerecorded.New(c)

  	// STEP 5: send/process file to Deepgram
  	res, err := dg.FromFile(ctx, filePath, &options)
  	if err != nil {
  		fmt.Printf("FromStream failed. Err: %v\n", err)
  		os.Exit(1)
  	}

  	// STEP 6: get the JSON response
  	data, err := json.Marshal(res)
  	if err != nil {
  		fmt.Printf("json.Marshal failed. Err: %v\n", err)
  		os.Exit(1)
  	}

  	// STEP 7: make the JSON pretty
  	prettyJson, err := prettyjson.Format(data)
  	if err != nil {
  		fmt.Printf("prettyjson.Marshal failed. Err: %v\n", err)
  		os.Exit(1)
  	}
  	fmt.Printf("\n\nResult:\n%s\n\n", prettyJson)
  }
  ```
</CodeGroup>

### Remote File Request

This example shows how to analyze a **remote audio file** (a URL that hosts your audio file).

<CodeGroup>
  ```javascript JavaScript
  const { createClient } = require("@deepgram/sdk");

  const transcribeUrl = async () => {
    // STEP 1: Create a Deepgram client using the API key
    const deepgram = createClient(process.env.DEEPGRAM_API_KEY);

    // STEP 2: Call the transcribeUrl method with the audio payload and options
    const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
      {
        url: "https://dpgr.am/spacewalk.wav",
      },
      // STEP 3: Configure Deepgram options for audio analysis
      {
        model: "nova-3",
        sentiment: true,
        // intents: true,
        // summarize: "v2",
        // topics: true,
      }
    );

    if (error) throw error;
    // STEP 4: Print the results
    if (!error) console.dir(result, { depth: null });
  };

  transcribeUrl();
  ```

  ```python Python
  # For help migrating to the new Python SDK, check out our migration guide:
  # https://github.com/deepgram/deepgram-python-sdk/blob/main/docs/Migrating-v3-to-v5.md

  import os
  from dotenv import load_dotenv

  from deepgram import (
      DeepgramClient,
  )

  load_dotenv()

  API_KEY = os.getenv("DEEPGRAM_API_KEY")

  def main():
      try:
          # STEP 1 Create a Deepgram client using the API key
          deepgram = DeepgramClient(api_key=API_KEY)

          # STEP 2: Call the transcribe_url method with the audio URL and options
          response = deepgram.listen.v1.media.transcribe_url(
              url="https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav",
              model="nova-2",
              sentiment=True,
              # intents=True,
              # summarize="v2",
              # topics=True,
          )

          # STEP 4: Print the response
          print(response.to_json(indent=4))

      except Exception as e:
          print(f"Exception: {e}")

  if __name__ == "__main__":
      main()
  ```

  ```go Go
  package main

  import (
  	"context"
  	"encoding/json"
  	"fmt"
  	"os"

  	prettyjson "github.com/hokaccha/go-prettyjson"

  	prerecorded "github.com/deepgram/deepgram-go-sdk/pkg/api/prerecorded/v1"
  	interfaces "github.com/deepgram/deepgram-go-sdk/pkg/client/interfaces"
  	client "github.com/deepgram/deepgram-go-sdk/pkg/client/prerecorded"
  )

  // URL to the audio file to analyze
  const (
  	url string = "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
  )

  func main() {
  	// STEP 1: init Deepgram client library
  	client.InitWithDefault()

  	// STEP 2: define context to manage the lifecycle of the request
  	ctx := context.Background()

  	// STEP 3: define options for the request
  	options := interfaces.PreRecordedTranscriptionOptions{
  		Model:     "nova-2",
  		Sentiment: true,
  		// Summarize: "v2",
  		// Topics: true,
  		// Intents:  true,
  	}

  	// STEP 4: create a Deepgram client using default settings
  	c := client.NewWithDefaults()
  	dg := prerecorded.New(c)

  	// STEP 5: send/process file to Deepgram
  	res, err := dg.FromURL(ctx, url, options)
  	if err != nil {
  		fmt.Printf("FromURL failed. Err: %v\n", err)
  		os.Exit(1)
  	}

  	// STEP 6: get the JSON response
  	data, err := json.Marshal(res)
  	if err != nil {
  		fmt.Printf("json.Marshal failed. Err: %v\n", err)
  		os.Exit(1)
  	}

  	// STEP 7: make the JSON pretty
  	prettyJson, err := prettyjson.Format(data)
  	if err != nil {
  		fmt.Printf("prettyjson.Marshal failed. Err: %v\n", err)
  		os.Exit(1)
  	}
  	fmt.Printf("\n\nResult:\n%s\n\n", prettyJson)
  }
  ```
</CodeGroup>

### Start the Application

Run your application from the terminal.

<CodeGroup>
  ```shell JavaScript
  # Run your application using the file you created in the previous step
  # Example: node index.js
  node index.js
  ```

  ```shell Python
  # Run your application using the file you created in the previous step
  # Example: python deepgram_test.py
  python YOUR_PROJECT_NAME.py
  ```

  ```shell Go
  # Run your application using the file you created in the previous step
  # Example: go run main.go

  go run YOUR_PROJECT_NAME.go
  ```
</CodeGroup>

### See Results

Your results will appear in your shell.

## Analyze the Response

When the file is finished processing (often after only a few seconds), you’ll receive a JSON response. (Note that some sections are omitted in order to demonstrate relevant properties.)

<CodeGroup>
  ```json summarization
  {
    "metadata": {
      ...
      "summary_info": {
        "model_uuid": "67875a7f-c9c4-48a0-aa55-5bdb8a91c34a",
        "input_tokens": 133,
        "output_tokens": 57
      }
    },
    "results": {
      "channels": [
        {
          "alternatives": [
            {
              "transcript": "Parker Scarves. How may I help you? I bought a scarf online for my wife, and it turns out they shipped the wrong color. Oh, I am so sorry, sir. I got it for her birthday, which is tonight, and now I I'm not a hundred percent sure what I need to do.",
              "confidence": 0.99902344,
              "words": [
                {
                  "word": "parker",
                  "start": 1.04,
                  "end": 1.52,
                  "confidence": 0.94628906,
                },
                ...
              ]
            }
          ]
        }
      ],
      "summary": {
        "result": "success",
        "short": "The customer called to complain about a scarf he ordered online for his wife's birthday. He explains that he bought the wrong color and now he is unsure what to do. The agent asks for the item number and color of the scarf he wants to purchase and offers to help."
      }
    }
  }
  ```

  ```json topic detection
  {
    "metadata": {
      ...
      "topics_info": {
        "model_uuid": "ba5b22e4-b39a-4550-a4bc-d8655f5092bc",
        "input_tokens": 140,
        "output_tokens": 8
      }
    },
    "results": {
      "channels": [
        {
          "alternatives": [
            {
              "transcript": "Parker Scarves. How may I help you? I bought a scarf online for my wife, and it turns out they shipped the wrong color.",
              "confidence": 0.99902344,
              "words": [
                {
                  "word": "parker",
                  "start": 1.04,
                  "end": 1.52,
                  "confidence": 0.94628906,
                  "punctuated_word": "Parker"
                },
  						...
              ]
            }
          ]
        }
      ],
      "topics": {
        "segments": [
          {
            "text": "I bought a scarf online for my wife, and it turns out they shipped the wrong color.",
            "start_word": 7,
            "end_word": 23,
            "topics": [
              { "topic": "Scarf wrong color", "confidence_score": 0.00060707016 }
            ]
          },
          {
            "text": "What color did you want the New Yorker in?",
            "start_word": 88,
            "end_word": 96,
            "topics": [{ "topic": "Ordering", "confidence_score": 0.1257968 }]
          }
        ]
      }
    }
  }
  ```

  ```json intent recognition
  {
    "metadata": {
      ...
      "intents_info": {
        "model_uuid": "80ab3179-d113-4254-bd6b-4a2f96498695",
        "input_tokens": 140,
        "output_tokens": 8
      }
    },
    "results": {
      "channels": [
        {
          "alternatives": [
            {
              "transcript": "Parker Scarves. How may I help you? I bought a scarf online for my wife, and it turns out they shipped the wrong color. Oh, I am so sorry, sir. I got it for her birthday, which is tonight, and now I I'm not a hundred percent sure what I need to do. Okay. Let me see if I can help you. Do you have the item number of the Parker scarf? I don't I don't think so. It it's called the New Yorker, I think. Excellent. Okay. What color did you want the New Yorker in? Blue. The one they shipped was like",
              "confidence": 0.99902344,
              "words": [
                {
                  "word": "parker",
                  "start": 1.04,
                  "end": 1.52,
                  "confidence": 0.94628906,
                  "punctuated_word": "Parker"
                }
                ...
              ]
            }
          ]
        }
      ],
      "intents": {
        "segments": [
          {
            "text": "I bought a scarf online for my wife, and it turns out they shipped the wrong color.",
            "start_word": 7,
            "end_word": 23,
            "intents": [
              {
                "intent": "Resolve scarf order issue",
                "confidence_score": 0.030428033
              }
            ]
          }
        ]
      }
    }
  }
  ```

  ```json sentiment analysis
  {
    "metadata": {
      ...
      "sentiment_info": {
        "model_uuid": "ba5b22e4-b39a-4550-a4bc-d8655f5092bc",
        "input_tokens": 140,
        "output_tokens": 140
      }
    },
    "results": {
      "channels": [
        {
          "alternatives": [
            {
              "transcript": "Parker Scarves. How may I help you? I bought a scarf online for my wife, and it turns out they shipped the wrong color. Oh, I am so sorry, sir. I got it for her birthday, which is tonight, and now I I'm not a hundred percent sure what I need to do. Okay. Let me see if I can help you. Do you have the item number of the Parker scarf? I don't I don't think so. It it's called the New Yorker, I think. Excellent. Okay. What color did you want the New Yorker in? Blue. The one they shipped was like",
              "confidence": 0.99902344,
              "words": [
                {
                  "word": "parker",
                  "start": 1.04,
                  "end": 1.52,
                  "confidence": 0.9482422,
                  "punctuated_word": "Parker",
                  "sentiment": "neutral",
                  "sentiment_score": 0.12397058308124542
                },
                {
                  "word": "scarves",
                  "start": 1.52,
                  "end": 1.92,
                  "confidence": 0.9173177,
                  "punctuated_word": "Scarves.",
                  "sentiment": "neutral",
                  "sentiment_score": 0.08247601985931396
                }
                ...
              ]
            }
          ]
        }
      ],
      "sentiments": {
        "segments": [
          {
            "text": "Parker Scarves. How may I help you? I bought a scarf online for my wife, and it turns out they shipped the wrong color.",
            "start_word": 0,
            "end_word": 23,
            "sentiment": "neutral",
            "sentiment_score": -0.15885239839553833
          },
          {
            "text": "Oh, I am so sorry, sir. I got it for her birthday, which is tonight, and now I I'm not a hundred percent sure what I need to do.",
            "start_word": 24,
            "end_word": 52,
            "sentiment": "negative",
            "sentiment_score": -0.37117594480514526
          }
          ...
        ],
        "average": {
          "sentiment": "neutral",
          "sentiment_score": -0.13682733263288224
        }
      }
    }
  }
  ```
</CodeGroup>

Following are explanations of each of the example responses. Be sure to click the tabs in the code block above to view the example response for each text analysis feature.

### All Audio Intelligence Features

Because Deepgram transcribes the audio before conducting the analysis, you will always see properties related to the transcription response, such as the following.

In the `results` object, we see:

* `transcript`: the transcript for the audio segment being processed.
* `confidence`: a floating point value between 0 and 1 that indicates overall transcript reliability. Larger values indicate higher confidence.
* `words`: an object containing each `word` in the transcript, along with its `start` time and `end` time (in seconds) from the beginning of the audio stream, and a `confidence` value.

### Summarization

In the `metadata` object, we see:

* `summary_info`: information about the model used and the input/output tokens. Summarization pricing is based on the number of input and output tokens. Read more at [deepgram.com/pricing](https://deepgram.com/pricing).
* `summary`: the `short` property in this object gives you the summary of the audio you requested to be analyzed.

### Topic Detection

In the `metadata` object, we see:

* `topics_info`: information about the model used and the input/output tokens. Topic Detection pricing is based on the number of input and output tokens. Read more at [deepgram.com/pricing](https://deepgram.com/pricing).

In the `results` object, we see:

* `topics`(object): contains the data about Topic Detection.

* `segments`: each segment object contains a span of text taken from the transcript; this `text` segment is analyzed for its topic.

* `topics`(array): a list of topic objects, each containing the `topic` and a `confidence_score`.

  * `topic`: Deepgram analyzes the segmented transcript to identify the main topic of each.
  * `confidence_score`: a floating point value between 0 and 1 indicating the overall reliability of the analysis.

### Intent Recognition

In the `metadata` object, we see:

* `intents_info`: information about the model used and the input/output tokens. Intent Recognition pricing is based on the number of input and output tokens. Read more at [deepgram.com/pricing](https://deepgram.com/pricing).

In the `results` object, we see:

* `intents`(object): contains the data about Intent Recognition.

* `segments`: each segment object contains a span of text taken from the transcript; this `text` segment is analyzed for its intent.

* `intents`(array): a list of intent objects, each containing the `intent` and a `confidence_score`.

  * `intent`: Deepgram analyzes the segmented transcript to identify the intent of each.
  * `confidence_score`: a floating point value between 0 and 1 indicating the overall reliability of the analysis.

### Sentiment Analysis

In the `metadata` object, we see:

* `sentiment_info`: information about the model used and the input/output tokens. Sentiment Analysis pricing is based on the number of input and output tokens. Read more at [deepgram.com/pricing](https://deepgram.com/pricing).

In the `results` object, we see:

* `sentiments`(object): contains the data about Sentiment Analysis.
* `segments`: each segment object contains a span of text taken from the transcript; these segments of text show when the sentiment shifts throughout the text, and each one is analyzed for its sentiment.
* `sentiment` can be `positive`, `negative`, or `neutral`.
* `sentiment_score`: a floating point value between -1 and 1 representing the sentiment of the associated span of text, with -1 being the most negative sentiment, and 1 being the most positive sentiment.
* `average`: the average sentiment for the entire transcript.

## Limits

### Language

At this time, audio analysis features only work for English language transcriptions.

### Token Limit

The input token limit is 150K tokens. When that limit is exceeded, a `400` error will be thrown

<CodeGroup>
  ```json JSON
  {
    "err_code": "TOKEN_LIMIT_EXCEEDED",
    "err_msg": "Text input currently supports up to 150K tokens. Please revise your text input to fit within the defined token limit. For more information, please visit our API documentation.",
    "request_id": "XXXX"
  }
  ```
</CodeGroup>
