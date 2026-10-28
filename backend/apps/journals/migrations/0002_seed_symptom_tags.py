from django.db import migrations

DEFAULT_SYMPTOMS = [
    ("Anxiety", "Persistent worry, nervousness, or unease."),
    ("Low mood", "Sadness, hopelessness, or flat affect."),
    ("Insomnia", "Difficulty falling or staying asleep."),
    ("Fatigue", "Low energy or persistent tiredness."),
    ("Irritability", "Being easily frustrated or short-tempered."),
    ("Difficulty concentrating", "Trouble focusing or staying on task."),
    ("Appetite change", "Eating noticeably more or less than usual."),
    ("Social withdrawal", "Avoiding friends, family, or social situations."),
    ("Panic", "Sudden, intense episodes of fear or physical panic symptoms."),
    ("Racing thoughts", "Thoughts that feel fast, intrusive, or hard to control."),
]


def seed_symptoms(apps, schema_editor):
    SymptomTag = apps.get_model("journals", "SymptomTag")
    for name, description in DEFAULT_SYMPTOMS:
        SymptomTag.objects.get_or_create(name=name, defaults={"description": description})


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_symptoms, noop_reverse),
    ]
