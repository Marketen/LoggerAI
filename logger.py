from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
from urllib.parse import parse_qs
import docker
import os
import openai

from dotenv import load_dotenv

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            message = '''
            <html>
            <head>
                <title>Form</title>
                <style>
                    body {
                        background-color: #F5F5F5;
                        text-align: center;
                    }
                    form {
                        margin-top: 50px;
                        display: inline-block;
                        text-align: left;
                        background-color: #FFFFFF;
                        border-radius: 10px;
                        padding: 20px;
                        box-shadow: 0px 0px 10px #888888;
                    }
                    label {
                        display: block;
                        margin-bottom: 10px;
                    }
                    input {
                        margin-bottom: 10px;
                        border-radius: 5px;
                        border: 1px solid #CCCCCC;
                        padding: 5px;
                    }
                    button {
                        margin-top: 10px;
                        background-color: #4CAF50;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 5px;
                        padding: 10px;
                        cursor: pointer;
                    }
                </style>
            </head>
            <body>
                <form method="post" action="/submit">
                    <label for="container_id">Container ID:</label>
                    <input type="text" name="container_id" id="container_id" required><br>
                    <label for="what_to_ask">What to ask:</label>
                    <input type="text" name="what_to_ask" id="what_to_ask"><br>
                    <label for="lines_to_read">Amount of log lines to read: </label>
                    <input type="text" name="lines_to_read" id="lines_to_read"><br>
                    <button type="submit" name="submit" value="start">Start</button>
                </form>
            </body>
            </html>
            '''
            self.wfile.write(message.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/submit':
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            if ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers.get('content-length'))
                load_dotenv()
                # postvars es un dict amb container_id i what_to_ask amb values string
                postvars = parse_qs(self.rfile.read(length).decode(), keep_blank_values=1)
                container_id = postvars["container_id"]
                what_to_ask = postvars["what_to_ask"]
                lines_to_read = postvars["lines_to_read"]
                lines_to_read[0] = int(lines_to_read[0])
                openai.api_key = os.getenv('GPT_KEY')
                openai.Model.list()
                # create a Docker client object
                client = docker.from_env()

                # specify the container ID or name whose logs you want to read
                container_id_or_name = ' '.join(container_id)
                container = client.containers.get(container_id_or_name)

                # initialize the last line variable to None
                #last_line = None
                #start_time = int(time.time()) - 120
                # stream the logs in real-time
                logs = container.logs(tail=lines_to_read[0], stream=False)
                error_lines = ""
                for line in logs.splitlines():
                    # decode the line from a byte string to a Unicode string
                    line = line.strip().decode("utf-8")
                    # check if the line contains "WARN" or "ERROR" (case-insensitive)
                    if "WARN" in line.upper() or "ERROR" in line.upper():
                        error_lines += line + "<br>"

                print("Last 50 lines read:")
                print("Error lines: " + error_lines)

                if what_to_ask == "":
                    completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": what_to_ask + "\n" + error_lines}
                    ]
                    )
                else:  
                    completion = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": "What do these logs of this ethereum-related client mean? Give me a brief explanation aswell as a possible solution. Also, determine if the error is critical or not" + error_lines}
                        ]
                    )

                print(completion.choices[0].message.content)

                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                message = f'''
                <html>
                    <head>
                        <title>AI results</title>
                        <style>
                            body {{
                                background-color: #f2f2f2;
                                font-family: Arial, sans-serif;
                                text-align: center;
                            }}
                            p {{
                                margin: 10px;
                                padding: 10px;
                                background-color: #fff;
                                border-radius: 5px;
                                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
                            }}
                            button {{
                                margin-top: 20px;
                                padding: 10px 20px;
                                background-color: #4CAF50;
                                color: #fff;
                                border: none;
                                border-radius: 5px;
                                font-size: 16px;
                                cursor: pointer;
                            }}
                            button:hover {{
                                background-color: #3e8e41;
                            }}
                        </style>
                    </head>
                    <body>
                        <h2>Container ID:</h2>
                        <p>{container_id}</p>
                        <h2>Number of log lines read: </h2>
                        <p>{lines_to_read}</p>
                        <h2>Logs</h2>
                        <p>{error_lines}</p>
                        <br>
                        <h1>AI response</h1>
                        <p>{completion.choices[0].message.content}</p>
                        <button onclick="window.location.href='/';">Back to Home</button>
                    </body>
                </html>
                '''
                self.wfile.write(message.encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid content-type for POST request!\n')
        else:
            self.send_error(404)


httpd = HTTPServer(("localhost", 8000), MyHandler)
print("Server started on http://localhost:8000")
httpd.serve_forever()
