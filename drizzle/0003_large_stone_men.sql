CREATE TABLE `archive_media` (
	`id` text PRIMARY KEY NOT NULL,
	`record` text NOT NULL,
	`file` text NOT NULL,
	FOREIGN KEY (`record`) REFERENCES `archive_records`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`file`) REFERENCES `intake_files`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `archive_media_record_file` ON `archive_media` (`record`,`file`);--> statement-breakpoint
CREATE TABLE `archive_records` (
	`id` text PRIMARY KEY NOT NULL,
	`intake` text NOT NULL,
	`name` text NOT NULL,
	`aliases` text DEFAULT '' NOT NULL,
	`region` text DEFAULT '' NOT NULL,
	`city` text DEFAULT '' NOT NULL,
	`summary` text NOT NULL,
	`body` text NOT NULL,
	`sources` text NOT NULL,
	`verification` text NOT NULL,
	`allow_export` integer DEFAULT 0 NOT NULL,
	`status` text DEFAULT 'published' NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`created` integer NOT NULL,
	`updated` integer NOT NULL,
	FOREIGN KEY (`intake`) REFERENCES `intake`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `archive_status_updated` ON `archive_records` (`status`,`updated`);--> statement-breakpoint
CREATE TABLE `intake` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text DEFAULT '' NOT NULL,
	`receipt_hash` text NOT NULL,
	`kind` text NOT NULL,
	`title` text NOT NULL,
	`institution` text DEFAULT '' NOT NULL,
	`region` text DEFAULT '' NOT NULL,
	`body` text NOT NULL,
	`source_note` text DEFAULT '' NOT NULL,
	`scope` text DEFAULT 'review' NOT NULL,
	`rights` integer DEFAULT 0 NOT NULL,
	`allow_export` integer DEFAULT 0 NOT NULL,
	`status` text DEFAULT 'draft' NOT NULL,
	`decision` text DEFAULT '' NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`created` integer NOT NULL,
	`updated` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `intake_status_updated` ON `intake` (`status`,`updated`);--> statement-breakpoint
CREATE INDEX `intake_owner_updated` ON `intake` (`owner`,`updated`);--> statement-breakpoint
CREATE TABLE `intake_events` (
	`id` text PRIMARY KEY NOT NULL,
	`intake` text NOT NULL,
	`action` text NOT NULL,
	`message` text NOT NULL,
	`created` integer NOT NULL,
	FOREIGN KEY (`intake`) REFERENCES `intake`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `intake_events_intake` ON `intake_events` (`intake`,`created`);--> statement-breakpoint
CREATE TABLE `intake_files` (
	`id` text PRIMARY KEY NOT NULL,
	`intake` text NOT NULL,
	`name` text NOT NULL,
	`mime` text NOT NULL,
	`size` integer NOT NULL,
	`storage_key` text NOT NULL,
	`sha256` text NOT NULL,
	`public_allowed` integer DEFAULT 0 NOT NULL,
	`export_allowed` integer DEFAULT 0 NOT NULL,
	`status` text DEFAULT 'ready' NOT NULL,
	`created` integer NOT NULL,
	FOREIGN KEY (`intake`) REFERENCES `intake`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `intake_files_intake` ON `intake_files` (`intake`);