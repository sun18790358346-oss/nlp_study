# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent LLM-based Werewolf game system where AI agents play against each other in the classic social deduction game. The system simulates the game with strict information isolation between roles.

## Architecture

### Core Components

1. **Game Engine (Judge)** - Drives the state machine for day/night cycles, collects decisions from agents in structured JSON format, and determines win/loss conditions.

2. **Multi-Agent Framework** - Each player is an independent LLM agent. Uses LangGraph, AutoGen, or custom architecture. Each agent has:
   - Independent memory system
   - Private context preventing "cheating" (e.g., wolves don't know other roles)
   - Chain-of-thought logging for observability

3. **Information Isolation Model**:
   - Wolves know their teammates but not other roles
   - Good players have no prior knowledge of others
   - Strict private context per agent

4. **Structured Logging** - Records agent thoughts, speech drafts, and strategy modifications for analysis.

### Game Rules (Standard 6-player variant)

**Win Conditions:**
- Good team: Eliminate all wolves
- Wolf team: Kill all gods OR all villagers (ping strategies)

**Roles & Night Actions:**
- **Werewolf**: Night kill one player (wolves coordinate via private channel)
- **Seer**: Check one player per night → returns "good" or "wolf" only
- **Witch**: One heal (resurrect tonight's death) + one poison (kill any player), each usable once, cannot save self
- **Hunter**: If killed at night or voted day, can shoot one player before dying (blocked if poisoned)
- **Villager**: No night ability, only day reasoning and voting

**Day Flow:**
1. Sheriff election (optional) → sheriff has 1.5 vote and decides speech order
2. Announce deaths (last words from eliminated players)
3. Public speech (each player argues their case)
4. Public vote to eliminate

**Special Rules:**
- If wolf self-reports during day, game immediately enters night
- Hunter cannot shoot if poisoned by witch

## Project Structure

```
├── agent/          # Multi-agent framework (agent definitions, coordination)
├── api/            # External API interfaces
├── configs/        # Configuration files
├── data/           # Data storage
├── game_engine/    # Game engine (judge), state machine, turn flow
├── logs/           # Game logs, agent thought logs
├── memory/         # Agent memory system, private context
├── roles/          # Role definitions (Werewolf, Seer, Witch, Hunter, Villager)
├── tests/          # Unit tests
└── utils/          # Utility functions
```

## Development Notes

- Frontend UI for spectating is optional enhancement
- Three advanced directions: Self-evolution (self-modifying prompts), Leaderboard/replay analysis, RLAIF self-improvement loop
- All agents should output structured JSON decisions for the game engine to parse