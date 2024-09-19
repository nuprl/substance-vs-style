# Running evaluation

To run `run_eval.py` in a docker container using Podman, follow these steps.

## Build image

To build the image, from within this directory run:

```bash 
podman image build -f Dockerfile -t studenteval ..
```

## Check Image

To check that the `studenteval` image was built successfully, run:

```bash
podman image ls
```

To view files in the image, you can run:

```bash
podman run -it studenteval /bin/sh
```

## Running

Create a directory for your input/ouputs, eg. `test_docker`:

```bash
mkdir test_docker
```

Move your input dataset (e.g. `StudentEval`) into the `test_docker` directory.

```bash
mv StudentEval test_docker/
```

To run the evaluation, use the following command:

```bash
podman run --rm --network none -v ./test_docker:/studenteval_nlp/test_docker studenteval python3 run_eval.py ./test_docker/StudentEval test_docker/output_eval_ds --split test
```