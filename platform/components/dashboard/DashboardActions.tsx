
import { Input } from "@/components/ui/input";
import { ResizablePanel } from "@/components/ui/resizable";
import { Textarea } from "@/components/ui/textarea";
import React, { useState } from "react";
import { Button } from "../ui/button";
import { runScript } from "@/lib/api.service";
import { toast } from "sonner";
  

const DashboardDisplay = ({ filePath, setScriptOutput, file, setFile } : { filePath: string, setScriptOutput: any, file: string, setFile: any }) => {
    const [repoName, setRepoName] = useState('');
    const [script, setScript] = useState('');
    const [instructions, setInstructions] = useState('');
    const [isLoading, setIsLoading] = useState(false)

    const updateRepoName = (event: any) => {
        setRepoName(event.target.value);
    }
    const updateScript = (event: any) => {
        setScript(event.target.value);
    }
    const updateInstructons = (event: any) => {
        setInstructions(event.target.value);
    }
    const runScriptWrapper = async (event: any) => {
        const response = await runScript(repoName, filePath, script);
        console.log("run script response", response)
        let scriptOutput = response.stdout + "\n" + response.stderr
        if (response.code != 0) {
            toast.error("An Error Occured", {
                description: [<div>Stdout:</div>, <div>{response.stdout}</div>, <div>Stderr:</div>, <div>{response.stderr}</div>,]
            })
        } else {
            toast.success("The script ran successfully", {
                description: [<div>Stdout:</div>, <div>{response.stdout}</div>, <div>Stderr:</div>, <div>{response.stderr}</div>,]
            })
        }
        setScriptOutput(scriptOutput)
    }
    const getFileChanges = async () => {
        setIsLoading(true)
        const url = "/api/openai/edit"
        const response = await fetch(url, {
            method: "POST",
            body: JSON.stringify({
                fileContents: file,
                prompt: instructions
            })
        })
        const object = await response.json();
        console.log(object)
        setIsLoading(false)
        toast("Successfully generated tests!")
        file = file + object.newFileContents;
        console.log("file is", file)
        setFile(file)
    }

    return (
        <ResizablePanel defaultSize={33} className="p-6 h-[80vh]">
            <div className="flex flex-col h-full">
                <Input id="name" placeholder="Enter Repository Name" value={repoName} className="col-span-4 w-full" onChange={updateRepoName}/>
                <Input className="mb-4" value="sweep/fix-branch"/>
                <Textarea id="instructions-input" placeholder="Edge cases for Sweep to cover." value={instructions} className="grow" onChange={updateInstructons}></Textarea>
                <Textarea id="script-input" placeholder="Enter your script here" className="col-span-4 w-full" value={script} onChange={updateScript}></Textarea>
                <div className="flex flex-row justify-center">
                    <Button className="mt-4" variant="secondary" onClick={runScriptWrapper}>Run tests</Button>
                    <Button 
                            className="mt-4 mr-4" 
                            variant="secondary" 
                            onClick={getFileChanges}
                        disabled={isLoading}
                    >Generate tests</Button>
                </div>
            </div>
        </ResizablePanel>
    );
};

export default DashboardDisplay;