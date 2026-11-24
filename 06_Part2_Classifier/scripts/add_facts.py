"""add_facts.py - "Did you know?" facts for the species that had none (the Part 1 classes already had them).

    python add_facts.py --pwa <pwa folder>

Facts are short, well-established statements; Uganda-specific ones name parks where the animal is
known to occur. Existing facts are never overwritten.
"""
import argparse, json
from pathlib import Path

FACTS = {
    "tiger": ["Tigers are the largest of all cat species.",
              "No two tigers have the same stripe pattern.",
              "Tigers come from Asia and do not live wild in Africa; in Uganda they are seen at UWEC in Entebbe.",
              "Unlike most cats, tigers like water and are strong swimmers."],
    "leopard": ["Leopards live in many of Uganda's national parks, including Queen Elizabeth and Murchison Falls.",
                "A leopard often carries its prey up into a tree to keep it away from lions and hyenas.",
                "Leopards are mostly active at night and are very hard to spot by day."],
    "fox": ["Foxes belong to the dog family.",
            "Their large ears help them hear small animals moving underground.",
            "Foxes usually hunt alone rather than in packs."],
    "frog": ["Frogs start life as tadpoles that live in water and breathe with gills.",
             "Many frogs can take in oxygen through their skin.",
             "The frog calls heard at night are mostly males calling to attract females."],
    "snake": ["Snakes have no eyelids and no external ears.",
              "A snake flicks its tongue to collect scents from the air.",
              "Uganda is home to pythons, cobras and vipers; the African rock python is Africa's largest snake."],
    "fish": ["Uganda shares Lake Victoria, Africa's largest lake, with Kenya and Tanzania.",
             "Tilapia and Nile perch are important food fish in Uganda.",
             "Fish breathe by taking oxygen from water through their gills."],
    "zebra": ["Every zebra has its own unique stripe pattern.",
              "In Uganda, zebras can be seen in Lake Mburo and Kidepo Valley National Parks.",
              "Zebras live in family groups and often graze together with other grazing animals."],
    "monkey": ["Uganda has a great variety of primates; Kibale Forest alone has 13 primate species.",
               "Monkeys have tails, which is one way to tell them apart from apes such as chimpanzees and gorillas.",
               "Vervet monkeys use different alarm calls for different predators."],
    "crocodile": ["The Nile crocodile is one of Africa's largest reptiles.",
                  "Many crocodiles can be seen along the Nile in Murchison Falls National Park.",
                  "Mother crocodiles carry their newly hatched young to the water in their mouths."],
    "tortoise": ["Some tortoises live for more than 100 years.",
                 "A tortoise's shell is part of its skeleton and cannot be taken off.",
                 "Tortoises live on land, while most turtles live in water."],
    "giraffe": ["The giraffe is the tallest land animal.",
                "Uganda's giraffes are Rothschild's (Nubian) giraffes, found in Murchison Falls, Kidepo Valley and Lake Mburo.",
                "A giraffe's long neck has the same number of bones (seven) as a human neck."],
    "rhino": ["Rhinos had disappeared from the wild in Uganda by the early 1980s.",
              "They have been brought back at Ziwa Rhino Sanctuary, where they are protected and breeding.",
              "A rhino's horn is made of keratin, the same material as human fingernails."],
    "squirrel": ["Squirrels use their bushy tails for balance when climbing and jumping.",
                 "Many squirrels bury food to eat later.",
                 "Africa has both tree squirrels and ground squirrels."],
    "lion": ["The Ishasha sector of Queen Elizabeth National Park is famous for lions that climb and rest in trees.",
             "Lions are the only cats that live in groups, called prides.",
             "A lion's roar can be heard several kilometres away."],
    "buffalo": ["African buffaloes live in large herds that protect their young together.",
                "They are considered one of the most dangerous animals in Africa, especially lone males.",
                "Buffaloes are common in Queen Elizabeth and Murchison Falls National Parks."],
    "cheetah": ["The cheetah is the fastest land animal, reaching about 100 km/h in short sprints.",
                "In Uganda, cheetahs are found mainly in Kidepo Valley National Park.",
                "Cheetahs cannot roar; they chirp, purr and growl instead."],
    "kudu": ["Male kudus have long spiral horns; only the males carry horns.",
             "The thin white stripes on a kudu's body help it hide in bushes.",
             "Kudus mostly eat leaves and shoots rather than grass."],
    "hyena": ["Spotted hyenas live in groups called clans, which are led by females.",
              "Hyenas hunt much of their own food; they do not only scavenge.",
              "The hyena's famous 'laugh' is a call it makes when excited or stressed."],
}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pwa", required=True); a = ap.parse_args()
    p = Path(a.pwa) / "model" / "species.json"
    sp = json.loads(p.read_text(encoding="utf-8"))
    n = 0
    for cls, facts in FACTS.items():
        if not sp[cls].get("facts"):
            sp[cls]["facts"] = facts; n += 1
    p.write_text(json.dumps(sp, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"facts added for {n} species; species without facts: "
          f"{[k for k, v in sp.items() if k != 'other' and not v.get('facts')]}")


if __name__ == "__main__":
    main()
