import time

from Factline.pipeline.pipeline import Pipeline


def main():

        # Topics are processed sequentially
    topics = [
        "india",
        "india+politics",
        "global",
        "sports",
        "economic",
        "entertainment"
    ]

    topic_index = 0

    while True:

        topic = topics[topic_index]

        pipeline = Pipeline()

        pipeline.run(topic)

        topic_index = (
            topic_index + 1
        ) % len(topics)

        time.sleep(2 * 60 * 60)


if __name__ == "__main__":
    main()
