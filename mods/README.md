# Моды для Stardew Valley (SMAPI)

15 модов, каждый в отдельной папке с логичным snake_case названием. Структура каждого мода:

```
<mod_name>/
├── manifest.json          — манифест SMAPI (название, UniqueID, EntryDll, версия)
├── <mod_name>.csproj      — проект .NET 6 (ModBuildConfig), сборка через `dotnet build`
├── *.cs                   — исходники (логика мода)
├── config.json            — настраиваемые параметры
├── data/*.json            — игровые данные (магазины, рецепты, таблицы)
├── i18n/ru.json, en.json  — переводы
└── assets/*.png           — иконки/спрайты
```

**Почему здесь нет .dll:** DLL — это бинарный результат компиляции `.cs` исходников.
Хранить в git можно только настоящую, собранную DLL; «DLL-файл для структуры» без
компилятора не существует (полноценного .NET SDK в этой среде нет). Поэтому заглушки
удалены, а рабочая DLL создаётся за пару команд при сборке (см. «Сборка» ниже) —
она появится в `bin/Release/net6.0/<mod_name>.dll`.

## Список модов

| # | Папка | Что делает |
|---|-------|------------|
| 1 | auto_sell_chest | Сундук мгновенной продажи с фильтрами и бонусом к цене |
| 2 | stamina_regen_aura | Тотемы, ускоряющие регенерацию энергии рядом с собой |
| 3 | weather_forecast_ui | Виджет прогноза погоды на 7 дней |
| 4 | quick_teleport_stones | Крафт телепорт-камней к любым точкам карты |
| 5 | smart_sprinkler_ai | Спринклеры поливают только сухую почву и нуждающиеся растения |
| 6 | pet_affection_overhaul | Баффы питомцев (кошка пугает ворон) + прокачка дружбы |
| 7 | crop_rotation_bonus | Плодородие почвы и бонусы за чередование культур |
| 8 | black_market | Ночной торговец редкими предметами за ресурсы |
| 9 | skill_specializations | Выбор специализаций навыков на 5/10 уровнях |
| 10 | seasonal_monster_invasion | Волны монстров на ферму в определённые сезоны |
| 11 | cooking_recipe_evolution | Рецепты улучшаются при частом приготовлении |
| 12 | community_board_2 | Динамические контракты гильдии под прогресс игрока |
| 13 | farm_layout_presets | Сохранение/мгновенная загрузка пресетов планировки (F7/F8) |
| 14 | infinite_water_hose | Бесконечный шланг у Пьера за 250 золотых: один конец в воду — и поливай |
| 15 | instant_fishing | Отмена мини-игры рыбалки: закинул удочку — сразу улов |

## Сборка (как получить настоящую DLL)

Заглушки в репозитории нет — DLL собирается из исходников. Нужен [.NET SDK 6](https://dotnet.microsoft.com/download/dotnet/6.0)
(или новее) и установленная игра Stardew Valley: ModBuildConfig сам найдёт папку игры и SMAPI-ссылки.

```bash
# 1) установить .NET SDK, если его нет
winget install Microsoft.DotNet.SDK.8        # Windows
# или: brew install dotnet                   # macOS
# или: sudo apt install dotnet-sdk-8.0       # Linux

# 2) собрать один мод
cd mods/<mod_name>
dotnet build -c Release

# 3) или собрать сразу все 15 модов
dotnet build Mods.sln -c Release
```

После сборки появится готовая структура мода для SMAPI:

```
mods/<mod_name>/bin/Release/net6.0/
├── <mod_name>.dll      ← настоящая, скомпилированная DLL
└── manifest.json       ← скопирован ModBuildConfig автоматически
```

Скопируйте папку `bin/Release/net6.0/` в `Mods/` игры (переименовав её в `<mod_name>`) —
либо используйте `<EnableModDeploy>true</EnableModDeploy>` (по умолчанию в ModBuildConfig
он уже включён), и тогда `dotnet build` сам разложит собранный мод в `Mods/` игры.
Запуск игры с [SMAPI](https://smapi.io) подхватит мод автоматически.

Если сборка ругается, что игра не найдена, укажите путь явно:

```bash
dotnet build -c Release /p:GamePath="D:/Steam/steamapps/common/Stardew Valley"
```

