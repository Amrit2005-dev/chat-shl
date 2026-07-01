import json
from test_hybrid import LocalRetriever, clean_text

r = LocalRetriever('catalog.json')
h = "Senior Full-Stack Engineer 5+ years across Core Java, Spring, REST API design, Angular, SQL/relational databases, AWS deployment, and Docker. Will own end-to-end microservice delivery, contribute to architectural decisions, and mentor mid-level engineers. Strong CI/CD and cloud-native experience required. Backend-leaning. Day-one priorities are Core Java and Spring; SQL is constant. Angular is occasional they'd review frontend PRs but not own features. Senior IC. They lead design on their own services but don't manage other engineers directly. Add AWS and Docker. Drop REST the API design signal will already come through in Spring and the live interview. On Java they'd be working on existing services, not greenfield. Is the Advanced level the right pick? Do we really need Verify G+ on top of all the technical tests? Feels redundant. Keep Verify G+. Locking it in."

print("Query words:", clean_text(h).split()[:20])

docker_item = next(it for it in r.items if 'docker-new' in it['url'])
print("\nDocker item:")
print("Name:", docker_item['item']['name'])
print("Name words:", docker_item['name_words'])
print("All words sample:", list(docker_item['all_words'])[:10])

# Compute score step-by-step
query_words = clean_text(h).split()
score = 0
name_overlap = []
desc_overlap = []
for w in query_words:
    if w in docker_item['name_words']:
        name_overlap.append(w)
        score += 15
    if w in docker_item['all_words']:
        desc_overlap.append(w)
        score += 2

print(f"Name overlap words: {name_overlap}")
print(f"Desc overlap words: {desc_overlap}")
print(f"Base score: {score}")

# Let's print the top 10 scoring items in catalog
scored = []
for it in r.items:
    it_score = 0
    name_lower = it['name_lower']
    for w in query_words:
        if w in it['name_words']:
            it_score += 15
        if w in it['all_words']:
            it_score += 2
    if name_lower in h.lower():
        it_score += 80
    for word in ["java", "python", "rust", "c++", "accounting", "statistics", "linux", "networking", "excel", "word", "hipaa", "medical", "retail", "sales", "safety", "help desk", "trainee"]:
        if word in h.lower() and word in name_lower:
            it_score += 100
    if it['item']['url'] in r.core_urls:
        it_score += 10
    scored.append((it_score, it['item']))

scored.sort(key=lambda x: x[0], reverse=True)
print("\nTop 15 scored items:")
for i, (sc, item) in enumerate(scored[:15]):
    print(f"{i+1}. Score={sc} | {item['name']} | {item['url']}")

print("\nWhere is Docker (New)?")
for i, (sc, item) in enumerate(scored):
    if 'docker' in item['name'].lower():
        print(f"Rank={i+1} | Score={sc} | {item['name']} | {item['url']}")
