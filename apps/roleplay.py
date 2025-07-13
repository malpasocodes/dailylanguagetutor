import streamlit as st
import random


def run_roleplay_app(client, model: str, language: str):
    """Run the roleplay application with the selected model and language."""
    
    # Initialize session state
    if "roleplay_active" not in st.session_state:
        st.session_state.roleplay_active = False
    if "roleplay_scenario" not in st.session_state:
        st.session_state.roleplay_scenario = None
    if "roleplay_character" not in st.session_state:
        st.session_state.roleplay_character = None
    if "roleplay_messages" not in st.session_state:
        st.session_state.roleplay_messages = []
    if "awaiting_retry" not in st.session_state:
        st.session_state.awaiting_retry = False
    if "correct_answer" not in st.session_state:
        st.session_state.correct_answer = ""
    if "show_translation" not in st.session_state:
        st.session_state.show_translation = {}
    
    # Display title
    st.title(f"🎭 Roleplay - {language}")
    st.caption(f"Using model: {model}")
    
    # Show scenario selection if not active
    if not st.session_state.roleplay_active:
        show_scenario_selection(client, model, language)
    else:
        # Show active roleplay
        show_roleplay_conversation(client, model, language)


def show_scenario_selection(client, model: str, language: str):
    """Display scenario selection interface."""
    
    st.markdown("## Choose a Roleplay Scenario")
    st.write("Select a scenario to practice your conversation skills:")
    
    # Predefined scenarios
    scenarios = {
        "🍽️ Restaurant": {
            "description": "Practice ordering food, asking about ingredients, and making requests at a restaurant",
            "character": "waiter/waitress",
            "setting": "restaurant"
        },
        "🗺️ Asking for Directions": {
            "description": "Learn to ask for and understand directions in the city",
            "character": "local resident",
            "setting": "street"
        },
        "🎉 Social Party": {
            "description": "Practice casual conversation, introductions, and small talk at a social gathering",
            "character": "party guest",
            "setting": "party"
        },
        "💼 Job Interview": {
            "description": "Prepare for job interviews with professional conversation practice",
            "character": "interviewer",
            "setting": "office"
        },
        "🏨 Hotel Check-in": {
            "description": "Practice hotel check-in, asking about amenities, and making requests",
            "character": "hotel receptionist",
            "setting": "hotel lobby"
        },
        "🛒 Shopping": {
            "description": "Learn to ask about prices, sizes, and make purchases",
            "character": "shop assistant",
            "setting": "store"
        },
        "🚕 Taking a Taxi": {
            "description": "Practice giving directions and communicating with taxi drivers",
            "character": "taxi driver",
            "setting": "taxi"
        },
        "🏥 Doctor's Appointment": {
            "description": "Learn medical vocabulary and how to describe symptoms",
            "character": "doctor",
            "setting": "clinic"
        }
    }
    
    # Display scenarios in a grid
    cols = st.columns(2)
    for i, (scenario_name, scenario_info) in enumerate(scenarios.items()):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"### {scenario_name}")
                st.write(scenario_info["description"])
                
                if st.button(f"Start {scenario_name}", key=f"scenario_{i}", use_container_width=True):
                    start_roleplay(client, model, language, scenario_name, scenario_info)
    
    st.markdown("---")
    
    # Custom scenario option
    st.markdown("### 🎨 Custom Scenario")
    custom_scenario = st.text_input(
        "Describe your own scenario:",
        placeholder="e.g., Buying tickets at a train station, Visiting a museum, etc."
    )
    
    if custom_scenario and st.button("Start Custom Scenario", type="primary"):
        custom_info = {
            "description": custom_scenario,
            "character": "appropriate role",
            "setting": "relevant location"
        }
        start_roleplay(client, model, language, f"🎨 {custom_scenario}", custom_info)


def start_roleplay(client, model: str, language: str, scenario_name: str, scenario_info: dict):
    """Initialize a new roleplay session."""
    
    with st.spinner("Starting roleplay..."):
        # Generate character introduction
        system_prompt = f"""You are a {scenario_info['character']} in a {scenario_info['setting']}. 
        The user wants to practice {language} conversation in this scenario: {scenario_info['description']}.
        
        IMPORTANT RULES:
        1. ONLY speak in {language} - never use English
        2. Stay in character as a {scenario_info['character']}
        3. Start by introducing yourself with a name and your role
        4. Ask an appropriate opening question for this scenario
        5. Keep responses conversational and natural
        6. If the user makes mistakes, provide the correct version and ask them to try again
        
        Begin the roleplay now by introducing yourself and asking an opening question."""
        
        try:
            # Get character introduction
            full_response = ""
            for chunk in client.chat_stream(
                model=model,
                messages=[{"role": "system", "content": system_prompt}],
                target_language=language
            ):
                full_response += chunk
            
            if full_response:
                # Store roleplay state
                st.session_state.roleplay_active = True
                st.session_state.roleplay_scenario = scenario_name
                st.session_state.roleplay_character = scenario_info
                st.session_state.roleplay_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "assistant", "content": full_response}
                ]
                st.session_state.awaiting_retry = False
                st.session_state.correct_answer = ""
                st.session_state.show_translation = {}
                
                st.rerun()
            else:
                st.error("Failed to start roleplay. Please try again.")
                
        except Exception as e:
            st.error(f"Error starting roleplay: {str(e)}")


def show_roleplay_conversation(client, model: str, language: str):
    """Display the active roleplay conversation."""
    
    # Header with scenario info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Scenario:** {st.session_state.roleplay_scenario}")
        st.markdown(f"**Character:** {st.session_state.roleplay_character['character']}")
    with col2:
        if st.button("🛑 End Roleplay", type="secondary"):
            end_roleplay()
            return
    
    st.markdown("---")
    
    # Display conversation
    for i, message in enumerate(st.session_state.roleplay_messages):
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar="🎭"):
                st.markdown(message["content"])
                
                # Add translate button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🔤 Translate", key=f"trans_{i}"):
                        if i not in st.session_state.show_translation:
                            with st.spinner("Translating..."):
                                translation = client.translate_to_english(
                                    model=model,
                                    text=message["content"],
                                    source_language=language
                                )
                                if translation:
                                    st.session_state.show_translation[i] = translation
                        else:
                            # Toggle off translation
                            del st.session_state.show_translation[i]
                        st.rerun()
                
                # Show translation if requested
                if i in st.session_state.show_translation:
                    st.info(f"**Translation:** {st.session_state.show_translation[i]}")
        
        elif message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
    
    # Show retry message if needed
    if st.session_state.awaiting_retry:
        st.warning(f"**Correct answer:** {st.session_state.correct_answer}")
        st.info("Please try again with the correct answer:")
    
    # User input
    user_input = st.chat_input(
        "Type your response in " + language + " (or 'Stop' to end)",
        key="roleplay_input"
    )
    
    if user_input:
        handle_user_input(client, model, language, user_input)


def handle_user_input(client, model: str, language: str, user_input: str):
    """Handle user input during roleplay."""
    
    # Check for stop command
    if user_input.lower().strip() in ["stop", "stop.", "arrêt", "alto", "halt", "stopp"]:
        end_roleplay()
        return
    
    # Add user message to conversation
    st.session_state.roleplay_messages.append({"role": "user", "content": user_input})
    
    with st.spinner("AI is responding..."):
        try:
            # Create prompt for AI response
            if st.session_state.awaiting_retry:
                # Check if the user provided the correct answer
                system_message = f"""The user was supposed to say: "{st.session_state.correct_answer}"
                They said: "{user_input}"
                
                If their answer is now correct or close enough, continue the conversation normally.
                If still incorrect, provide encouragement and the correct answer again, then ask them to try once more.
                Remember: ONLY speak in {language}."""
            else:
                # Normal conversation flow
                system_message = f"""Continue the roleplay as a {st.session_state.roleplay_character['character']}.
                Evaluate the user's response. If it's correct and natural, continue the conversation.
                If there are significant errors, provide the correct version and ask them to try again.
                Remember: ONLY speak in {language}."""
            
            # Get conversation history for context
            conversation = st.session_state.roleplay_messages.copy()
            conversation.append({"role": "system", "content": system_message})
            
            full_response = ""
            for chunk in client.chat_stream(
                model=model,
                messages=conversation,
                target_language=language
            ):
                full_response += chunk
            
            if full_response:
                # Add AI response
                st.session_state.roleplay_messages.append({"role": "assistant", "content": full_response})
                
                # Check if this is a correction (simple heuristic)
                if any(word in full_response.lower() for word in ["correct", "should", "try again", "instead", "correcto", "deberías", "korrekt", "solltest", "essayer"]):
                    # Extract the correct answer (this is a simple approach)
                    st.session_state.awaiting_retry = True
                    st.session_state.correct_answer = "See the AI's suggestion above"
                else:
                    st.session_state.awaiting_retry = False
                    st.session_state.correct_answer = ""
                
                st.rerun()
            else:
                st.error("Failed to get AI response. Please try again.")
                
        except Exception as e:
            st.error(f"Error getting response: {str(e)}")


def end_roleplay():
    """End the current roleplay session."""
    st.session_state.roleplay_active = False
    st.session_state.roleplay_scenario = None
    st.session_state.roleplay_character = None
    st.session_state.roleplay_messages = []
    st.session_state.awaiting_retry = False
    st.session_state.correct_answer = ""
    st.session_state.show_translation = {}
    
    st.success("Roleplay ended! Great job practicing!")
    st.rerun()