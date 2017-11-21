FROM python:3

WORKDIR /src

#dependencies
COPY REQUIREMENTS.txt ./
RUN pip install --no-cache-dir -r REQUIREMENTS.txt

#sources
COPY . .

#cmd
CMD [ "python", "./bot.py" ]