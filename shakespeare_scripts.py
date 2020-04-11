import mysql.connector
import numpy as np
import pandas as pd
import re
import getpass
from os import system as sys


class ShakespeareDB:
    """ Class for accessing the OSS database

    Attributes: 
        host (str): The IP address of the MySQL server (default: '127.0.0.1') 
        port (int): The port number of the MySQL server (default: 3306) 
        database (str): The name of the MySQL database (default: 'shakespeare') 
        user (str): The user for the MySQL database (default: logged in user)

    """

    def __init__(self, host='127.0.0.1', port=3306, database='shakespeare', user=getpass.getuser()):
        """Constructor for the DB object, defaults to MySQL Defaults for local DB"""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = getpass.getpass("Connecting as %s. Password: " % user)

    def open_connection(self):
        """Returns a connection object for querying the DB"""
        cnx = mysql.connector.connect(user=self.user, password=self.password,
                                      host=self.host, port=self.port,
                                      database=self.database)
        return cnx

    def get_title(self, WorkID):
        """Returns the title of the play given by WorkID"""
        cnx = self.open_connection()
        cursor = cnx.cursor()
        query = ("SELECT LongTitle FROM works " +
                 "WHERE WorkID = '" + WorkID + "'")
        cursor.execute(query)

        for result in cursor:
            return result[0]

    def get_scene_numbers(self, WorkID):
        """Returns the act and scene numbers with descriptions from the play given by WorkID"""
        cnx = self.open_connection()
        cursor = cnx.cursor()
        query = ("SELECT Section, Chapter, Description FROM chapters " +
                 "WHERE WorkID = '" + WorkID + "'")
        cursor.execute(query)

        scenes = []

        for result in cursor:
            scenes.append({'Section': str(result[0]), 'Chapter': str(
                result[1]), 'Description': result[2]})

        return scenes

    def get_scene(self, WorkID, Section, Chapter):
        """Returns the lines of the specified play scene"""
        cnx = self.open_connection()
        cursor = cnx.cursor()
        query = ("SELECT CharID, PlainText FROM paragraphs " +
                 "WHERE WorkID = '" + WorkID + "' " +
                 "AND Section = '" + Section + "' " +
                 "AND Chapter = '" + Chapter + "' ")

        result = cursor.execute(query)
        lines = []

        for result in cursor:
            lines.append({'CharID': result[0], 'PlainText': result[1]})

        # Perhaps check ordering, though should be ordered by ParagraphID
        return lines

    def get_characters(self, WorkID):
        """Returns a list of all characters and descriptions from the specified play"""
        cnx = self.open_connection()
        cursor = cnx.cursor()
        query = ("SELECT CharName, CharID, Description FROM characters " +
                 "WHERE Works = '" + WorkID + "'")

        result = cursor.execute(query)

        characters = []
        for result in cursor:
            characters.append({'Name': result[0],
                               'CharID': result[1],
                               'Description': result[2]})
        return(characters)


class ScriptTex:
    """Class for generating personalized scripts in tex

    Attributes:
        path (str): path to output script files
        filename (str): name of output file
    """

    def __init__(self, path, filename):
        """Constructor that sets the output file"""
        self.path = path
        self.file = filename

    def _callback(self, matches):
        """Callback function for decoding unicode references"""
        id = matches.group(1)
        try:
            # Special treatment to get apostrophes correctly
            if int(id) == 8217:
                return chr(39)
            else:
                return chr(int(id))
        except Exception as e:
            print(e)
            return id

    def decode_unicode_references(self, data):
        """Replaces unicode references using regex"""
        return re.sub("&#(\d+)(;|(?=\s))", self._callback, data)

    def add_preamble(self, title, author):
        """Adds preamble to .tex file, must be called before other 'add_' functions"""
        with open(self.path + self.file, 'w') as file:
            file.write(r'\documentclass[english]{article}'+'\n')
            file.write(r'\usepackage{textcomp}'+'\n')
            file.write(r'\usepackage{xcolor}'+'\n')
            file.write(r'\usepackage[english]{babel}'+'\n')
            file.write(r'\usepackage[pass,a5paper]{geometry}'+'\n')
            file.write(
                r'\usepackage[characterstyle=arden, xspace=true,actlevel=chapter,scenelevel=section]{thalie}'+'\n')
            file.write(r'\title{'+title+'}'+'\n')
            file.write(r'\author{'+author+'}'+'\n')
            file.write(r'\date{}'+'\n')
            file.write(r'\begin{document}'+'\n')
            file.write(r'\maketitle'+'\n')

    def add_characters(self, characters):
        """Adds characters to .tex file"""
        with open(self.path + self.file, 'a') as file:
            file.write(r'\act*{Dramatis Personae}'+'\n')
            file.write(r'\begin{dramatis}'+'\n')
            for char in characters:
                id = re.sub('-ce', '', char['CharID'])
                file.write(
                    r'\character[cmd='+id+', desc={'+char["Description"]+'}]{'+char['Name']+'}\n')
            file.write(r'\end{dramatis}'+'\n')

    def add_lines(self, lines, highlight):
        """Adds lines to .tex file, highlighting lines belonging to characters specified in highlight"""
        with open(self.path + self.file, 'a') as file:
            for line in lines:
                if line['CharID'] == 'xxx':  # xxx signifies stage directions
                    text = re.sub('\[p\]', '', line['PlainText'])
                    text = re.sub('[\[\]]', '', text)
                    file.write(r'\begin{dida}'+text+r'\end{dida}'+'\n')
                else:  # Otherwise is a character's line
                    # Parse the DB into tex-formatted text
                    text = re.sub('\n\[p\]', '\\\\\\\\\n', line['PlainText'])
                    text = re.sub('\]([\s\S]+\])', '\\1', text)
                    text = re.sub('\[([\s\S]+)\]', '\\\did{\\1}', text)
                    text = re.sub('[\[\]]', '', text)

                    id = re.sub('-ce', '', line['CharID'])

                    if line['CharID'] in highlight:
                        file.write(r'\color{violet}'+'\n')

                    file.write('\\' + id + '\n' + text+'\n')
                    if line['CharID'] in highlight:
                        file.write(r'\color{black}'+'\n')

    def add_act(self):
        """Adds act markup to .tex file"""
        with open(self.path + self.file, 'a') as file:
            file.write(r'\newpage'+'\n')
            file.write(r'\act{}'+'\n')

    def add_scene(self, description):
        """Adds scene and description markup to .tex file"""
        with open(self.path + self.file, 'a') as file:
            file.write(r'\scene{}'+'\n')
            file.write(
                r'\onstage{'+self.decode_unicode_references(description)+'}'+'\n')

    def add_direction(self, direction):
        """Adds stage direction markup to .tex file"""
        with open(self.path + self.file, 'a') as file:
            file.write(r'\begin{dida}'+direction+r'\end{dida}'+'\n')

    def end(self):
        """Ends the .tex file"""
        with open(self.path + self.file, 'a') as file:
            file.write(r'\end{document}'+'\n')

    def make_pdf(self):
        """Uses lualatex to convert .tex file to pdf"""
        sys('lualatex -output-directory='+self.path+' '+self.file)
