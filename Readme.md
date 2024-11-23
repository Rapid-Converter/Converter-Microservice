# Doc2Pdf

The is the main service which utilizes the `unoserver` to convert the doc files to pdf files.

There are 2 routes:

- /convert - which takes a docx file, converts it to a pdf. If encryption is true, then sends the pdf to Encryption-Service for the encryption.
  Even if the Encryption-Service is down, a pdf will be generated without any encryption.

- /list-pdfs - gives a list of all the converted pdfs

## Running the app

#### Steps to run the app:

- run `./converter_script.sh`

## Running the stack

To run the whole stack, use this [Dockerfile](https://github.com/Rapid-Converter/Deployments/blob/master/docker-compose.yml).
`docker compose up -d --build`

## Technologies/Libraries Used

- Python
- FastAPI
- unoconv
