bl_info = {
    "name": "GPT Blender",
    "author": "Embedded Networking Laboratory",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "",
    "description": "Instant 3D content generation via LLM",
    "warning": "",
    "doc_url": "",
    "category": "3D content generation",
}

import bpy
from bpy.props import StringProperty, PointerProperty, CollectionProperty
from bpy.types import Panel, Operator, PropertyGroup
from bpy.utils import register_class, unregister_class
from g4f.client import Client

class GPTBlender_HistoryEntry(PropertyGroup):
    role: StringProperty(name="Role")
    content: StringProperty(name="Content")

class GPTBlender_Properties(PropertyGroup):
    prompt: StringProperty(
        name="Prompt",
        description="User's prompt",
        default="",
        maxlen=4096,
    )
    history: CollectionProperty(type=GPTBlender_HistoryEntry)
    
    full_response: StringProperty(
        name="Full Response",
        description="All responses concatenated",
        default="",
    )

class GPTBlender_Operator(bpy.types.Operator):
    bl_idname = "genai.1"
    bl_label = "Generative AI Operator"
    
    def __init__(self):
        self.client = Client()

    def execute(self, context):
        user_input = context.scene.GPTBlender_prop.prompt
        new_prompt = {"role": "user", "content": user_input}
        result = self.generate_response(context.scene.GPTBlender_prop.history, new_prompt)
        print(result)
        
        context.scene.GPTBlender_prop.full_response += result + "\n"
        
        print(self.code_check(context.scene.GPTBlender_prop.full_response))
        
        return {'FINISHED'}
    
    def code_check(self, full_response):
        messages = [
            {"role": "system", "content": "You're an assistant expert in Blender code. Check the code and give me a correct program."},
            {"role": "user", "content": full_response},
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=messages
        )
        correct_program = response.choices[0].message.content
        
        return correct_program
    
    def handle_response(self, response_content):
        try:
            exec(response_content)
        except Exception as e:
            self.report({'ERROR'}, f"Execution error: {e}")

    def generate_response(self, history, new_prompt):
        messages = [
            {"role": "system", "content": "You're an assistant to help in Blender code. Your job is help user writting a full Blender program in Python"},
        ]
        messages.extend([{"role": entry.role, "content": entry.content} for entry in history])
        messages.append(new_prompt)
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=messages
        )
        
        response_content = response.choices[0].message.content

        user_entry = history.add()
        user_entry.role = "user"
        user_entry.content = new_prompt['content']

        assistant_entry = history.add()
        assistant_entry.role = "assistant"
        assistant_entry.content = response_content
        
        return response_content
    

class GPTBlender_ClearHistoryOperator(bpy.types.Operator):
    bl_idname = "genai.clear_history"
    bl_label = "Clear History Operator"

    def execute(self, context):
        context.scene.GPTBlender_prop.history.clear()
        print("Chat history cleared.")
        return {'FINISHED'}        

class GPTBlender_Panel(bpy.types.Panel):
    bl_label = "GPT Blender Panel"
    bl_idname = "OBJECT_PT_GPTBlender"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GPT Blender"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        GPTBlenderProp = scene.GPTBlender_prop
        layout.prop(GPTBlenderProp, "prompt")
        row = layout.row()
        row.operator(GPTBlender_Operator.bl_idname, text="Generate", icon='SHADERFX')
        row = layout.row()
        row.operator(GPTBlender_ClearHistoryOperator.bl_idname, text="Clear History", icon='X')

_classes = [
    GPTBlender_HistoryEntry,
    GPTBlender_Properties,
    GPTBlender_Operator,
    GPTBlender_ClearHistoryOperator,
    GPTBlender_Panel
]

def register():
    for cls in _classes:
        register_class(cls)
    bpy.types.Scene.GPTBlender_prop = PointerProperty(type=GPTBlender_Properties)

def unregister():
    for cls in _classes:
        unregister_class(cls)
    del bpy.types.Scene.GPTBlender_prop

if __name__ == "__main__":
    register()
