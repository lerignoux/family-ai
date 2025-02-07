FROM node:lts-alpine3.19

RUN mkdir /app
COPY ./ /app

WORKDIR /app/family-ai

RUN npm i -g @quasar/cli
RUN npm install --proxy=http://192.168.2.3:6665

CMD ["quasar", "dev"]
