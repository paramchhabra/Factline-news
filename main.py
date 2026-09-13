from Factline.pipeline.pipeline import Pipeline
from Factline.utils.helper import read_config, read_state, write_state


def main():

    config = read_config()
    state = read_state()

    topics = config.topics
    topic_index = state["current_topic_index"]

    topic = topics[topic_index]

    pipeline = Pipeline()

    pipeline.run(topic)

    next_index = (
        topic_index + 1
    ) % len(topics)

    state["current_topic_index"] = next_index

    write_state(state)



if __name__ == "__main__":
    main()