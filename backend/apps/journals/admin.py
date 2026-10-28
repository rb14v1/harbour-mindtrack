from django.contrib import admin

from apps.journals.models import JournalEntry, JournalEntryEdit, JournalEntrySymptom, MoodScore, SymptomTag

admin.site.register(SymptomTag)
admin.site.register(JournalEntry)
admin.site.register(MoodScore)
admin.site.register(JournalEntrySymptom)
admin.site.register(JournalEntryEdit)
