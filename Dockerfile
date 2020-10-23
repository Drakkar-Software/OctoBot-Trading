FROM python:3.8-slim-stretch

ENV LOGS_DIR="logs" \
    BUILD_DEPS="build-essential"

# Set up octobot's environment
COPY . /trading-bot
WORKDIR /trading-bot

# install dependencies
RUN apt-get update \
  && apt-get install -qq -y --no-install-recommends $BUILD_DEPS \
  && apt-get clean -yq \
  && apt-get autoremove -yq \
  && rm -rf /var/lib/apt/lists/*

# configuration and installation
RUN pip3 install cython \
    && pip3 install -r requirements.txt -r dev_requirements.txt

# tests
#RUN pytest tests

VOLUME /trading-bot/$LOGS_DIR

ENTRYPOINT ["python", "./cli/cli.py"]
