#!/usr/bin/env python3

# Food Accumulator Tool Copyright 2016

import argparse
import shlex
import parsedatetime
import numbers
import numpy as np
from collections import namedtuple, defaultdict
from datetime import datetime
from bisect import bisect
from pprint import pformat


# Food Accumulator Tool Script:
#
# ingredient butter --unit=cup --amt=1 --kcal=1628 --carbs=0.1 --fat=184 --protein=1.9
# ingredient milk_2% --unit=cup --amt=1 --kcal=122 --carbs=12.3 --fat=4.8 --protein=8.1
# ingredient cheese_cheddar_mild --unit=g --amt=28 --kcal=110 --carbs=0 --fat=9 --protein=7
# ingredient boxmac --unit=serving --amt=1 --kcal=250 --carbs=47 --fat=3 --protein=9
# combine "cheesy mac" butter 0.25 milk_2% 0.2 boxmac 1.5 cheese_cheddar_mild 60 #optional --amt=1 --unit=serving (defaults)
# eat 1463977331 "cheesy mac" #optional --amt=2 (default: 1)

class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)

cal = parsedatetime.Calendar()

ingredParser = ThrowingArgumentParser(description="Define an ingredient")
ingredParser.add_argument("name")
ingredParser.add_argument("--unit", "-u", required=True)
ingredParser.add_argument("--amt", "-a", type=float, required=True)
ingredParser.add_argument("--kcal", "-C", type=float, required=True)
ingredParser.add_argument("--carbs", "-c", type=float, required=True)
ingredParser.add_argument("--fat", "-f", type=float, required=True)
ingredParser.add_argument("--protein", "-p", type=float, required=True)

combineParser = ThrowingArgumentParser(description="Define a combination")
combineParser.add_argument("name")
combineParser.add_argument("ingredList", nargs="+")
combineParser.add_argument("--amt", "-a", type=float, default=1.0)
combineParser.add_argument("--unit", "-u", default="serving")

eatParser = ThrowingArgumentParser(description="Eat some food")
eatParser.add_argument("time", type=float)
eatParser.add_argument("item")
eatParser.add_argument("--amt", "-a", type=float, default=1.0)


class Meal(namedtuple("Meal", ["time","name","amt","kcal","carbs","fat","protein"])):
    def __str__(self):
        return repr(type(self)(
            time = str(datetime.fromtimestamp(self.time)),
            name = self.name,
            amt = self.amt,
            kcal = round(self.kcal),
            carbs = round(self.carbs, 1),
            fat = round(self.fat, 1),
            protein = round(self.protein, 1)
            ))


class Ingredient(namedtuple("Ingredient", ["name","contents","unit","kcal","carbs","fat","protein"])):

    Sub = namedtuple("Sub", ["name", "amt"])

    def __str__(self):
        return repr(type(self)(
            name = self.name,
            contents = self.contents,
            unit = self.unit,
            kcal = round(self.kcal, 1),
            carbs = round(self.carbs, 2),
            fat = round(self.fat, 2),
            protein = round(self.protein, 2) ))

    def __mul__(self, scale):
        if not isinstance(scale, numbers.Number):
            raise TypeError("Only multiplication by a Number is supported")
        return type(self)(
                name = self.name,
                contents = tuple(self.Sub(i, a*scale) for i,a in self.contents),
                unit = self.unit,
                kcal = self.kcal * scale,
                carbs = self.carbs * scale,
                fat = self.fat * scale,
                protein = self.protein * scale )

    def __rmul__(self, other):
        return self.__mul__(other)

    @classmethod
    def fromArgs(cls, args):
        parsed = ingredParser.parse_args(args)
        return cls(parsed.name,
                   (),
                   parsed.unit,
                   parsed.kcal / parsed.amt,
                   parsed.carbs / parsed.amt,
                   parsed.fat / parsed.amt,
                   parsed.protein / parsed.amt)
    

def combine(name, ingredients, amounts, unit):
    kcal = sum(i.kcal * a for i, a in zip(ingredients, amounts))
    carbs = sum(i.carbs * a for i, a in zip(ingredients, amounts))
    fat = sum(i.fat * a for i, a in zip(ingredients, amounts))
    protein = sum(i.protein * a for i, a in zip(ingredients, amounts))
    contents = tuple(Ingredient.Sub(i.name, a) for i, a in zip(ingredients, amounts))
    return Ingredient(name, contents, unit, kcal, carbs, fat, protein)


class FoodDB:
    def __init__(self, filenames=[]):
        self.ingredients = {}
        self.eaten = []
        self._integrateFiles(filenames)
        if len(self.eaten) > 0:
            self.begin = datetime.fromtimestamp(self.eaten[0].time)
        else:
            self.begin = datetime.fromtimestamp(0)
        self.end = datetime.now()

    def __str__(self):
        span = "{} to {}".format(self.begin, self.end)
        ingred = "\n".join("  " + str(i) for i in sorted(self.ingredients.values(), key=lambda x: x.name))
        eaten = "\n".join("  " + str(e) for e in self.eaten)
        return "{}\nIngredients:\n{}\nEaten:\n{}".format(span, ingred, eaten)

    def _parseLine(self, line):
        args = shlex.split(line, comments=True)
        if len(args) == 0:
            return
        try:
            command = args[0]
            commandArgs = args[1:]
        except IndexError:
            raise ValueError("Bad line: {}".format(line))
        try:
            if command == "ingredient":
                self._accumIngredient(commandArgs)
            elif command == "combine":
                self._accumCombine(commandArgs)
            elif command == "eat":
                self._accumEat(commandArgs)
            else:
                raise ValueError("Unknown command: {}".format(command))
        except ValueError as e:
            raise ValueError("Bad line: {}, {}".format(line, e))

    def _accumIngredient(self, args):
        newIngred = Ingredient.fromArgs(args)
        assert newIngred.name not in self.ingredients
        self.ingredients[newIngred.name] = newIngred

    def _accumCombine(self, args):
        parsed = combineParser.parse_args(args)
        assert len(parsed.ingredList) % 2 == 0
        components = [self.ingredients[x] for x in parsed.ingredList[::2]]
        amounts = [float(a) for a in parsed.ingredList[1::2]]
        assert parsed.name not in self.ingredients
        newIngred = combine(parsed.name, components, amounts, parsed.unit)
        newIngred = 1/parsed.amt * newIngred
        self.ingredients[newIngred.name] = newIngred

    def _accumEat(self, args):
        parsed = eatParser.parse_args(args)
        assert parsed.item in self.ingredients
        ingredItem = self.ingredients[parsed.item]
        meal = Meal(parsed.time,
                    parsed.item,
                    parsed.amt,
                    parsed.amt * ingredItem.kcal,
                    parsed.amt * ingredItem.carbs,
                    parsed.amt * ingredItem.fat,
                    parsed.amt * ingredItem.protein)
        self.eaten.append(meal)

    def _integrateFiles(self, filenames):
        lines = []
        for fn in filenames:
            with open(fn) as file:
                for line in file:
                    self._parseLine(line)
        self.eaten.sort(key=lambda m: m.time)

    def filteredRange(self, begin, end):
        """Get a FoodDB view that contains meals from the speficied timespan.
        
        Parameters
        ==========
        begin : datetime
            start of interval
        end : datetime
            end of interval
        """
        result = type(self)()
        keys = [x.time for x in self.eaten]
        first = bisect(keys, begin.timestamp())
        after = bisect(keys, end.timestamp())
        result.ingredients = self.ingredients
        result.eaten = self.eaten[first:after]
        result.begin = begin
        result.end = end
        return result

    def totalStats(self):
        """Calculate the total kilocalories and macro ratios for this FoodDB.

        Returns
        =======
        kcal
            Total Calorie intake
        carbs
            Percent energy from carbs
        fat
            Percent energy from fat
        protein
            Percent energy from protein
        """
        totCal = 0
        totCarbCal = 0
        totFatCal = 0
        totProtCal = 0
        for meal in self.eaten:
            totCal += meal.kcal
            totCarbCal += meal.carbs * 4
            totFatCal += meal.fat * 9
            totProtCal += meal.protein * 4
        totMacroCal = sum((totCarbCal, totFatCal, totProtCal))
        return namedtuple("TotalStats",["kcal","carbs","fat","protein"])(
            totCal,
            100 * totCarbCal / totMacroCal,
            100 * totFatCal / totMacroCal,
            100 * totProtCal / totMacroCal)

    def meanDailyStats(self):
        """Calculate the mean daily statistics for this FoodDB.

        Returns
        =======
        kcal
            Average daily Calorie intake
        carbs
            Percent energy from carbs
        fat
            Percent energy from fat
        protein
            Percent energy from protein
        """
        deltaDays = (self.end - self.begin).total_seconds() / (3600*24)
        deltaDays = max(1, deltaDays) #daily stats nonsensical <1 day, avoid /0
        total = self.totalStats()
        return namedtuple("MeanDailyStats",["kcal","carbs","fat","protein"])(
            total.kcal / deltaDays,
            *total[1:])

    def blameMeals(self):
        def mealCGen():
            for meal in self.eaten:
                vec = np.array((meal.kcal, meal.carbs, meal.fat, meal.protein))
                yield (meal.name, vec)
        return self._blameTally(mealCGen)

    def blameIngredients(self):
        def recurseCGen(ingredSpec):
            ingred = self.ingredients[ingredSpec.name]
            if len(ingred.contents) == 0:
                vec = np.array((ingred.kcal, ingred.carbs, ingred.fat, ingred.protein))
                vec = vec * ingredSpec.amt
                yield (ingred.name, vec)
            else:
                for child in ingred.contents:
                    yield from recurseCGen(child)
        def ingredCGen():
            for meal in self.eaten:
                yield from recurseCGen(Ingredient.Sub(meal.name, meal.amt))
        return self._blameTally(ingredCGen)

    def _blameTally(self, culpritGen):
        """Find the critical meals/ingredients."""
        sources = defaultdict(lambda: np.zeros(4))
        totals = np.zeros(4)
        for culprit, vec in culpritGen():
            sources[culprit] += vec
            totals += vec
        #convert to percent
        sources = { k: v/totals * 100 for k,v in sources.items() }
        #Make leaderboards
        kcalSort = sorted( ((k,v[0]) for k,v in sources.items()), key=lambda x: -x[1])
        carbSort = sorted( ((k,v[1]) for k,v in sources.items()), key=lambda x: -x[1])
        fatSort = sorted( ((k,v[2]) for k,v in sources.items()), key=lambda x: -x[1])
        proteinSort = sorted( ((k,v[3]) for k,v in sources.items()), key=lambda x: -x[1])
        return namedtuple("Culprits",["kcal", "carbs", "fat", "protein"])(
                kcalSort,
                carbSort,
                fatSort,
                proteinSort)

def doBlame(db):
    for mode, fun in [("Ingredients", db.blameIngredients), ("Meals", db.blameMeals)]:
        result = fun()
        print("{}:".format(mode))
        for nutrient, leaderboard in result._asdict().items():
            print("  {}".format(nutrient))
            for culprit, percent in leaderboard[:5]:
                print("    {:25} {:4.1f}%".format(culprit, percent))

def printStatsObject(stats):
    print("Calories {:6.1f}".format(stats.kcal))
    print("Carbs   {:6.1f}%".format(stats.carbs))
    print("Fat     {:6.1f}%".format(stats.fat))
    print("Protein {:6.1f}%".format(stats.protein))

def doSummary(db):
    print(" Daily Average")
    printStatsObject(db.meanDailyStats())

def zeroHourToday():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

def doToday(db):
    """Print today's kcal total and macro ratios."""
    begin = zeroHourToday()
    end = datetime.now()
    filtered = db.filteredRange(begin, end)
    print(filtered)
    print("")
    print("Today".center(15))
    printStatsObject(filtered.totalStats())

def doTimeSeries(db):
    raise NotImplementedError

if __name__ == "__main__":
    # Arguments
    mainParser = argparse.ArgumentParser(description="Analyze food log")
    mainParser.add_argument("command", choices=["dump","blame","summary","today","time_series"])
    mainParser.add_argument("file", nargs="+")
    mainParser.add_argument("--begin-interval", "-b", help="Only consider food eaten after")
    mainParser.add_argument("--end-interval", "-e", help="Only consider food eaten before")
    args = mainParser.parse_args()
    # Load files
    db = FoodDB(args.file)
    # Figure out the filtering dates
    if args.begin_interval:
        begin = cal.parseDT(args.begin_interval)[0]
    else:
        begin = db.begin
    if args.end_interval:
        end = cal.parseDT(args.end_interval)[0]
    else:
        end = db.end
    # Filter
    db = db.filteredRange(begin, end)
    if args.command == "dump":
        print(db)
    elif args.command == "blame":
        doBlame(db)
    elif args.command == "summary":
        doSummary(db)
    elif args.command == "today":
        doToday(db)
    elif args.command == "time_series":
        doTimeSeries(db)
        
    

    




