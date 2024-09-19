FROM ubuntu:22.04
RUN apt-get update

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -yq install tzdata build-essential wget
RUN apt-get install -yq python3-pip
RUN pip3 install datasets pandas tqdm numpy
WORKDIR /studenteval_nlp
COPY eval_scripts/run_eval.py /studenteval_nlp
COPY utils.py /studenteval_nlp