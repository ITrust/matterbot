FROM python:3

WORKDIR /src

#dependencies
COPY REQUIREMENTS.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#sources
COPY . .

#cmd
CMD [ "python", "./bot.py" ]