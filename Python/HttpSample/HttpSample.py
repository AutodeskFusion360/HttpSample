#    (C) Copyright 2015 by Autodesk, Inc.
#    Permission to use, copy, modify, and distribute this software in
#    object code form for any purpose and without fee is hereby granted,
#    provided that the above copyright notice appears in all copies and
#    that both that copyright notice and the limited warranty and restricted
#    rights notice below appear in all supporting documentation.
#    
#    AUTODESK PROVIDES THIS PROGRAM "AS IS" AND WITH ALL FAULTS.
#    AUTODESK SPECIFICALLY DISCLAIMS ANY IMPLIED WARRANTY OF MERCHANTABILITY OR
#    FITNESS FOR A PARTICULAR USE. AUTODESK, INC. DOES NOT WARRANT THAT THE
#    OPERATION OF THE PROGRAM WILL BE UNINTERRUPTED OR ERROR FREE.

import adsk.core, adsk.fusion, traceback, json, http.client, webbrowser

handlers = []
repos = []
url = ''

def GetFusionRepositories():
    h = http.client.HTTPSConnection('api.github.com')
    headers = { 'User-Agent': 'Fusion360' }
    h.request('GET', '/users/autodeskfusion360/repos', '', headers)
    res = h.getresponse()
    
    resBytes = res.read() 
    resString = resBytes.decode('utf-8')
    resJson = json.loads(resString)
        
    return resJson

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Show the selected repository in the browser
        webbrowser.open_new(url)
        
        # Force the termination of the command.
        adsk.terminate()  
        
class CommandDeactivateHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # When the command is done, terminate the script
            # This will release all globals which will remove all event handlers
            adsk.terminate() 
        except:
            False

# On input change (i.e. when selection in combo changes)
# then update the description text field
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Code to react to the event.
        if args.input.id == 'repoList':
            repoList = args.input
            selItem = repoList.selectedItem
            index = selItem.index
        
            repoDescription = args.firingEvent.sender.commandInputs.itemById('repoDescription')
            repoDescription.formattedText = repos[index]['description']
            global url
            url = repos[index]['html_url']

class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        cmd = adsk.core.Command.cast(args.command)
        cmdInputs = cmd.commandInputs
                
        # Items
        repoList = cmdInputs.addDropDownCommandInput('repoList', 'Available Repositories', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
        # Fill it with items
        global repos
        repos = GetFusionRepositories()
        for item in repos:             
            repoList.listItems.add(item['name'], False, '', -1)
        # Select first item in the list
        repoList.listItems[0].isSelected = True
       
        # Description of the repository
        cmdInputs.addTextBoxCommandInput('repoDescription', 'Description', repos[0]['description'], 3, True)

        # Connect to the command executed event.        
        onExecute = CommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)
        
        # Connect to the command destroy event to clean up 
        onDestroy = CommandDeactivateHandler()
        cmd.destroy.add(onDestroy)
        handlers.append(onDestroy)
        
        # Check when the combo box selection changes
        onInputChanged = CommandInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # Create the command definition.
        if ui.commandDefinitions.itemById('fusionGitHubSamples'):
            ui.commandDefinitions.itemById('fusionGitHubSamples').deleteMe()            
        cmdDef = ui.commandDefinitions.addButtonDefinition('fusionGitHubSamples', 'Fusion GitHub', '', '')
        
        # Connect up to the command created event.
        onCommandCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        # execute the command.
        cmdDef.execute()
        
        # Keep the script running.
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))