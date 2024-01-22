
import { Input } from "@/components/ui/input";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { Textarea } from "@/components/ui/textarea";
import React from "react";
import CodeMirror from "@uiw/react-codemirror";
import { javascript } from "@codemirror/lang-javascript";
import { vscodeDark } from "@uiw/codemirror-theme-vscode";
import { Button } from "../ui/button";
import FileSelector from "../shared/FileSelector";
import DashboardSettings from "./DashboardSettings";
  

const DashboardDisplay = () => {
    const [value, setValue] = React.useState("console.log('hello world!');");
    const onChange = React.useCallback((val, viewUpdate) => {
        console.log('val:', val);
        setValue(val);
    }, []);
    return (
        <ResizablePanelGroup className="min-h-[80vh]" direction="horizontal">
            <ResizablePanel defaultSize={67}>
                <ResizablePanelGroup direction="vertical">
                    <ResizablePanel defaultSize={75} className="flex flex-col mb-4">
                        <FileSelector></FileSelector>
                        <Textarea className="mt-4 grow">
                            File content
                        </Textarea>
                    </ResizablePanel>
                    <ResizableHandle withHandle/>
                    <ResizablePanel defaultSize={25}>
                        <CodeMirror value={value} extensions={[javascript({ jsx: true })]} onChange={onChange} theme={vscodeDark} height="100%"/>
                    </ResizablePanel>
                </ResizablePanelGroup>
                </ResizablePanel>
            <ResizableHandle withHandle/>
            <ResizablePanel defaultSize={33} className="p-6 h-[80vh]">
                <div className="flex flex-col h-full">
                    <Input className="mb-4" value="sweep/fix-branch"/>
                    <Textarea placeholder="Edge cases for Sweep to cover." className="grow"></Textarea>
                    <div className="flex flex-row justify-center">
                        <DashboardSettings></DashboardSettings>
                        <Button className="mt-4 mr-4" variant="secondary">Generate tests</Button>
                        <Button className="mt-4" variant="secondary">Run tests</Button>
                    </div>
                </div>
            </ResizablePanel>
        </ResizablePanelGroup>
    );
};

export default DashboardDisplay;