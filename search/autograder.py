# autograder.py
# -------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

import grading
import importlib.util
import optparse
import os
import re
import sys
import projectParams
import random
random.seed(0)

try:
    from pacman import GameState
except ImportError:
    pass

ERROR_HINT_MAP = {
  'q1': {
    "<type 'exceptions.IndexError'>": """
      We noticed that your project threw an IndexError on q1.
      While many things may cause this, it may have been from
      assuming a certain number of successors from a state space
      or assuming a certain number of actions available from a given
      state. Try making your code more general (no hardcoded indices)
      and submit again!
    """
  },
  'q3': {
      "<type 'exceptions.AttributeError'>": """
        We noticed that your project threw an AttributeError on q3.
        While many things may cause this, it may have been from assuming
        a certain size or structure to the state space. For example, if you have
        a line of code assuming that the state is (x, y) and we run your code
        on a state space with (x, y, z), this error could be thrown. Try
        making your code more general and submit again!
    """
  }
}

# register arguments and set default values
def readCommand(argv):
    parser = optparse.OptionParser(description='Run public tests on student code')
    parser.set_defaults(generateSolutions=False, edxOutput=False, gsOutput=False, muteOutput=False, printTestCase=False, noGraphics=False)
    parser.add_option('--test-directory',
                      dest='testRoot',
                      default='test_cases',
                      help='Root test directory which contains subdirectories corresponding to each question')
    parser.add_option('--student-code',
                      dest='studentCode',
                      default=projectParams.STUDENT_CODE_DEFAULT,
                      help='comma separated list of student code files')
    parser.add_option('--code-directory',
                      dest='codeRoot',
                      default="",
                      help='Root directory containing the student and testClass code')
    parser.add_option('--test-case-code',
                      dest='testCaseCode',
                      default=projectParams.PROJECT_TEST_CLASSES,
                      help='class containing testClass classes for this project')
    parser.add_option('--generate-solutions',
                      dest='generateSolutions',
                      action='store_true',
                      help='Write solutions generated to .solution file')
    parser.add_option('--edx-output',
                      dest='edxOutput',
                      action='store_true',
                      help='Generate edX output files')
    parser.add_option('--gradescope-output',
                      dest='gsOutput',
                      action='store_true',
                      help='Generate GradeScope output files')
    parser.add_option('--mute',
                      dest='muteOutput',
                      action='store_true',
                      help='Mute output from executing tests')
    parser.add_option('--print-tests', '-p',
                      dest='printTestCase',
                      action='store_true',
                      help='Print each test case before running them.')
    parser.add_option('--test', '-t',
                      dest='runTest',
                      default=None,
                      help='Run one particular test.  Relative to test root.')
    parser.add_option('--question', '-q',
                      dest='gradeQuestion',
                      default=None,
                      help='Grade one particular question.')
    parser.add_option('--no-graphics',
                      dest='noGraphics',
                      action='store_true',
                      help='No graphics display for pacman games.')
    (options, args) = parser.parse_args(argv)
    return options

# confirm we should author solution files
def confirmGenerate():
    print('WARNING: this action will overwrite any solution files.')
    print('Are you sure you want to proceed? (yes/no)')
    while True:
        ans = sys.stdin.readline().strip()
        if ans == 'yes':
            break
        elif ans == 'no':
            sys.exit(0)
        else:
            print('please answer either "yes" or "no"')

def setModuleName(module, filename):
    functionType = type(confirmGenerate)
    classType = type(optparse.Option)

    for i in dir(module):
        o = getattr(module, i)
        if hasattr(o, '__file__'): continue

        if type(o) == functionType:
            setattr(o, '__file__', filename)
        elif type(o) == classType:
            setattr(o, '__file__', filename)

def loadModuleFile(moduleName, filePath):
    spec = importlib.util.spec_from_file_location(moduleName, filePath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def readFile(path, root=""):
    "Read file from disk at specified path and return as string"
    with open(os.path.join(root, path), 'r') as handle:
        return handle.read()

import pprint

def splitStrings(d):
    d2 = dict(d)
    for k in d:
        if k.startswith("__"):
            del d2[k]
            continue
        if '\n' in d2[k]:
            d2[k] = d2[k].split("\n")
    return d2

def printTest(testDict, solutionDict):
    pp = pprint.PrettyPrinter(indent=4)
    print("Test case:")
    for line in testDict["__raw_lines__"]:
        print("   |", line)
    print("Solution:")
    for line in solutionDict["__raw_lines__"]:
        print("   |", line)

def runTest(testName, moduleDict, printTestCase=False, display=None):
    import testParser
    import testClasses
    for module in moduleDict:
        setattr(sys.modules[__name__], module, moduleDict[module])

    testDict = testParser.TestParser(testName + ".test").parse()
    solutionDict = testParser.TestParser(testName + ".solution").parse()
    test_out_file = os.path.join('%s.test_output' % testName)
    testDict['test_out_file'] = test_out_file
    testClass = getattr(projectTestClasses, testDict['class'])

    questionClass = getattr(testClasses, 'Question')
    question = questionClass({'max_points': 0}, display)
    testCase = testClass(question, testDict)

    if printTestCase:
        printTest(testDict, solutionDict)

    grades = grading.Grades(projectParams.PROJECT_NAME, [(None, 0)])
    testCase.execute(grades, moduleDict, solutionDict)

def getDepends(testParser, testRoot, question):
    allDeps = [question]
    questionDict = testParser.TestParser(os.path.join(testRoot, question, 'CONFIG')).parse()
    if 'depends' in questionDict:
        depends = questionDict['depends'].split()
        for d in depends:
            allDeps = getDepends(testParser, testRoot, d) + allDeps
    return allDeps

def getTestSubdirs(testParser, testRoot, questionToGrade):
    problemDict = testParser.TestParser(os.path.join(testRoot, 'CONFIG')).parse()
    if questionToGrade is not None:
        questions = getDepends(testParser, testRoot, questionToGrade)
        if len(questions) > 1:
            print('Note: due to dependencies, the following tests will be run: %s' % ' '.join(questions))
        return questions
    if 'order' in problemDict:
        return problemDict['order'].split()
    return sorted(os.listdir(testRoot))

def evaluate(generateSolutions, testRoot, moduleDict, exceptionMap=ERROR_HINT_MAP,
             edxOutput=False, muteOutput=False, gsOutput=False,
             printTestCase=False, questionToGrade=None, display=None):
    import testParser
    import testClasses
    for module in moduleDict:
        setattr(sys.modules[__name__], module, moduleDict[module])

    questions = []
    questionDicts = {}
    test_subdirs = getTestSubdirs(testParser, testRoot, questionToGrade)
    for q in test_subdirs:
        subdir_path = os.path.join(testRoot, q)
        if not os.path.isdir(subdir_path) or q.startswith('.'):
            continue

        questionDict = testParser.TestParser(os.path.join(subdir_path, 'CONFIG')).parse()
        questionClass = getattr(testClasses, questionDict['class'])
        question = questionClass(questionDict, display)
        questionDicts[q] = questionDict

        tests = filter(lambda t: re.match(r'[^#~.].*\.test\Z', t), os.listdir(subdir_path))
        tests = map(lambda t: re.match(r'(.*)\.test\Z', t).group(1), tests)
        for t in sorted(tests):
            test_file = os.path.join(subdir_path, '%s.test' % t)
            solution_file = os.path.join(subdir_path, '%s.solution' % t)
            test_out_file = os.path.join(subdir_path, '%s.test_output' % t)
            testDict = testParser.TestParser(test_file).parse()
            if testDict.get("disabled", "false").lower() == "true":
                continue
            testDict['test_out_file'] = test_out_file
            testClass = getattr(projectTestClasses, testDict['class'])
            testCase = testClass(question, testDict)
            def makefun(testCase, solution_file):
                if generateSolutions:
                    return lambda grades: testCase.writeSolution(moduleDict, solution_file)
                else:
                    testDict = testParser.TestParser(test_file).parse()
                    solutionDict = testParser.TestParser(solution_file).parse()
                    if printTestCase:
                        return lambda grades: printTest(testDict, solutionDict) or testCase.execute(grades, moduleDict, solutionDict)
                    else:
                        return lambda grades: testCase.execute(grades, moduleDict, solutionDict)
            question.addTestCase(testCase, makefun(testCase, solution_file))

        def makefun(question):
            return lambda grades: question.execute(grades)
        setattr(sys.modules[__name__], q, makefun(question))
        questions.append((q, question.getMaxPoints()))

    grades = grading.Grades(projectParams.PROJECT_NAME, questions,
                            gsOutput=gsOutput, edxOutput=edxOutput, muteOutput=muteOutput)
    if questionToGrade is None:
        for q in questionDicts:
            for prereq in questionDicts[q].get('depends', '').split():
                grades.addPrereq(q, prereq)

    grades.grade(sys.modules[__name__], bonusPic=projectParams.BONUS_PIC)
    return grades.points

def getDisplay(graphicsByDefault, options=None):
    graphics = graphicsByDefault
    if options is not None and options.noGraphics:
        graphics = False
    if graphics:
        try:
            import graphicsDisplay
            return graphicsDisplay.PacmanGraphics(1, frameTime=.05)
        except ImportError:
            pass
    import textDisplay
    return textDisplay.NullGraphics()

def run(args):
    main(args.split()[1:])

def main(argv):
    options = readCommand(argv)
    if options.generateSolutions:
        confirmGenerate()
    codePaths = options.studentCode.split(',')

    moduleDict = {}
    for cp in codePaths:
        moduleName = re.match(r'.*?([^/]*)\.py', cp).group(1)
        moduleDict[moduleName] = loadModuleFile(moduleName, os.path.join(options.codeRoot, cp))
    moduleName = re.match(r'.*?([^/]*)\.py', options.testCaseCode).group(1)
    moduleDict['projectTestClasses'] = loadModuleFile(moduleName, os.path.join(options.codeRoot, options.testCaseCode))

    if options.runTest is not None:
        runTest(options.runTest, moduleDict, printTestCase=options.printTestCase, display=getDisplay(True, options))
    else:
        evaluate(options.generateSolutions, options.testRoot, moduleDict,
                 gsOutput=options.gsOutput,
                 edxOutput=options.edxOutput, muteOutput=options.muteOutput, printTestCase=options.printTestCase,
                 questionToGrade=options.gradeQuestion, display=getDisplay(options.gradeQuestion is not None, options))

if __name__ == '__main__':
    main(sys.argv)
