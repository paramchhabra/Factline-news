import os

from Factline.pipeline.pipeline import Pipeline
from Factline.utils.helper import (
    read_config,
    read_state,
    write_state
)
from Factline import logger


MAX_RETRIES = 3


def retry_operation(operation, operation_name):

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            return operation()

        except Exception:

            logger.exception(
                "%s failed. Attempt %d/%d",
                operation_name,
                attempt,
                MAX_RETRIES
            )

            if attempt == MAX_RETRIES:
                raise


def main():

    os.makedirs("artifacts/audio", exist_ok=True)
    os.makedirs("artifacts/images", exist_ok=True)
    os.makedirs("artifacts/videos", exist_ok=True)
    os.makedirs("logs/", exist_ok=True)

    config = read_config()

    state = retry_operation(
        read_state,
        "Reading pipeline state"
    )

    topics = config.topics
    topic_index = state["current_topic_index"]

    topic = topics[topic_index]
    
    pipeline = Pipeline()
    pipeline.run(topic, state)

    next_index = (topic_index + 1) % len(topics)

    state["current_topic_index"] = next_index
    state["session_id"] = None
    state["stage"] = "complete"

    write_state(state)


if __name__ == "__main__":
    main()