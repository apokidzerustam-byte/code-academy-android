# Идея и требования

```python
story = "Как студент, я хочу записывать расходы, чтобы понимать, куда уходят деньги"
role, rest = story.split(", я хочу ")
action, goal = rest.split(", чтобы ")
print(role, "|", action, "|", goal)

features = [("Задачи", 3), ("Расходы", 4), ("Экспорт", 2), ("Справка", 1)]
capacity = 8
chosen = []
for name, hours in features:
    if hours <= capacity:
        chosen.append(name)
        capacity -= hours
print(chosen, capacity)
```

1. Требование = роль + действие + цель.
2. MVP — только обязательное.
3. Критерий приёмки — то, что можно проверить.
