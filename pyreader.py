import docker
import time
import os
import openai
import requests
import json
import itertools

import cgi

form = cgi.FieldStorage()

input1 = form.getvalue("input1")
input2 = form.getvalue("input2")

output = "Input 1: " + input1 + "<br>Input 2: " + input2

print("Content-type: text/html\n")
print(output)


# openai.organization = "org-qmzZW5Gms1V93XSzjMxMaFh3"
openai.api_key = "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"
openai.Model.list()
# create a Docker client object
client = docker.from_env()

# specify the container ID or name whose logs you want to read
container_id_or_name = "1bdc292b0621"
container = client.containers.get(container_id_or_name)

# initialize the last line variable to None
last_line = None
start_time = int(time.time())
# stream the logs in real-time
logs = container.logs(stream=True, since=start_time)

# read each line of the logs
error_lines = ""
for batch in itertools.islice(logs, 10):
    # decode the line from a byte string to a Unicode string
    batch = batch.strip().decode("utf-8")
    # check if the line contains "WARN" or "ERROR" (case-insensitive)
    if "WARN" in batch.upper() or "ERROR" in batch.upper():
        error_lines += batch + "\n"

print("10 lines read:")
print(error_lines)

completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "What does this log line of a geth client mean? Give me a brief explanation aswell as a possible solution. Also, determine if the error is critical or not" + error_lines}
    ]
)

print(completion.choices[0].message.content)


with open("errors.txt", "w") as f:
    # write some text to the file
    f.write("Execution client errors:")
    f.write(error_lines)
    f.write(completion.choices[0].message.content)
    f.write("\n")
    